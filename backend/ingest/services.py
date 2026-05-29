from django.db import transaction
from django.utils import timezone

from .models import ActivityRecord, AuditEvent, IngestionBatch
from .parsers import PARSERS


def ingest_uploaded_file(*, organization, source, uploaded_file, user) -> IngestionBatch:
    parser = PARSERS.get(source.source_type)
    if not parser:
        raise ValueError(f"No parser for source type {source.source_type}")

    batch = IngestionBatch.objects.create(
        organization=organization,
        source=source,
        uploaded_by=user,
        original_filename=uploaded_file.name,
        status=IngestionBatch.Status.PROCESSING,
    )

    try:
        rows = parser(uploaded_file.read())
    except Exception as exc:
        batch.status = IngestionBatch.Status.FAILED
        batch.error_summary = str(exc)
        batch.save(update_fields=["status", "error_summary"])
        AuditEvent.objects.create(
            organization=organization,
            batch=batch,
            actor=user,
            action=AuditEvent.Action.INGEST,
            note=f"Batch failed: {exc}",
        )
        return batch

    success = 0
    errors = 0
    warnings = 0
    records = []

    for row in rows:
        flags = row.get("validation_flags") or []
        if flags:
            warnings += 1
        if row.get("parse_ok"):
            success += 1
        else:
            errors += 1

        records.append(
            ActivityRecord(
                organization=organization,
                batch=batch,
                source=source,
                scope=row["scope"],
                category=row["category"],
                activity_date=row.get("activity_date"),
                period_start=row.get("period_start"),
                period_end=row.get("period_end"),
                facility_code=row.get("facility_code", ""),
                vendor_or_carrier=row.get("vendor_or_carrier", ""),
                description=row.get("description", ""),
                quantity=row.get("quantity"),
                unit=row.get("unit", ""),
                normalized_quantity=row.get("normalized_quantity"),
                normalized_unit=row.get("normalized_unit", ""),
                spend_amount=row.get("spend_amount"),
                spend_currency=row.get("spend_currency", ""),
                origin=row.get("origin", ""),
                destination=row.get("destination", ""),
                distance_km=row.get("distance_km"),
                raw_payload=row.get("raw_payload", {}),
                source_row_hash=row["source_row_hash"],
                source_reference=row.get("source_reference", ""),
                parse_ok=row.get("parse_ok", False),
                validation_flags=flags,
                validation_message=row.get("validation_message", ""),
            )
        )

    with transaction.atomic():
        ActivityRecord.objects.bulk_create(records)
        batch.row_count = len(rows)
        batch.success_count = success
        batch.error_count = errors
        batch.warning_count = warnings
        batch.status = IngestionBatch.Status.COMPLETED
        batch.save()
        AuditEvent.objects.create(
            organization=organization,
            batch=batch,
            actor=user,
            action=AuditEvent.Action.INGEST,
            after_state={
                "row_count": batch.row_count,
                "success_count": success,
                "error_count": errors,
                "warning_count": warnings,
            },
            note=f"Ingested {uploaded_file.name}",
        )

    return batch


def review_record(*, record: ActivityRecord, user, action: str, note: str = "") -> ActivityRecord:
    if record.is_locked_for_audit:
        raise ValueError("Record is locked for audit")

    before = {
        "review_status": record.review_status,
        "validation_flags": record.validation_flags,
    }

    if action == "approve":
        record.review_status = ActivityRecord.ReviewStatus.APPROVED
        record.is_locked_for_audit = True
        audit_action = AuditEvent.Action.APPROVE
    elif action == "reject":
        record.review_status = ActivityRecord.ReviewStatus.REJECTED
        audit_action = AuditEvent.Action.REJECT
    else:
        raise ValueError("Unsupported review action")

    record.reviewed_by = user
    record.reviewed_at = timezone.now()
    record.save()

    AuditEvent.objects.create(
        organization=record.organization,
        record=record,
        actor=user,
        action=audit_action,
        before_state=before,
        after_state={"review_status": record.review_status, "locked": record.is_locked_for_audit},
        note=note,
    )
    return record
