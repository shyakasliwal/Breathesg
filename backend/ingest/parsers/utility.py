from datetime import timedelta

from .common import (
    convert_to_kwh,
    normalize_row_keys,
    parse_date,
    parse_decimal,
    read_csv_rows,
    row_hash,
)


def _pick(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row and row[key]:
            return row[key]
    return ""


def parse_utility_csv(file_bytes: bytes) -> list[dict]:
    rows = [normalize_row_keys(r) for r in read_csv_rows(file_bytes)]
    parsed = []

    for idx, row in enumerate(rows, start=2):
        account = _pick(row, "account_number", "account", "service_account")
        meter = _pick(row, "meter_id", "meter", "meter_number")
        site = _pick(row, "site_code", "facility", "location_id")
        usage = parse_decimal(_pick(row, "usage", "consumption", "kwh", "usage_kwh"))
        unit = _pick(row, "usage_unit", "unit") or "kWh"
        period_start = parse_date(_pick(row, "billing_period_start", "period_start", "from_date"))
        period_end = parse_date(_pick(row, "billing_period_end", "period_end", "to_date"))
        tariff = _pick(row, "tariff", "rate_schedule")
        supplier = _pick(row, "utility_name", "supplier", "provider")

        flags = []
        if usage is None:
            flags.append("missing_usage")
        if period_start is None or period_end is None:
            flags.append("billing_period_gap")
        if period_start and period_end and period_end < period_start:
            flags.append("inverted_billing_period")

        normalized_qty, normalized_unit = convert_to_kwh(usage, unit)
        if period_start and period_end:
            span_days = (period_end - period_start).days + 1
            if span_days > 45:
                flags.append("long_billing_period")
            if span_days < 20:
                flags.append("short_billing_period")

        if usage is not None and usage > 500000:
            flags.append("suspiciously_high_usage")

        activity_date = period_end
        if period_start and period_end and (period_end - period_start) > timedelta(days=40):
            flags.append("non_calendar_month_period")

        parse_ok = "missing_usage" not in flags

        parsed.append(
            {
                "scope": "scope_2",
                "category": "electricity",
                "activity_date": activity_date,
                "period_start": period_start,
                "period_end": period_end,
                "facility_code": site or account,
                "vendor_or_carrier": supplier,
                "description": f"Electricity ({tariff})" if tariff else "Electricity",
                "quantity": usage,
                "unit": unit,
                "normalized_quantity": normalized_qty,
                "normalized_unit": normalized_unit or "",
                "spend_amount": parse_decimal(_pick(row, "total_charge", "amount", "bill_total")),
                "spend_currency": _pick(row, "currency") or "USD",
                "origin": meter,
                "destination": "",
                "distance_km": None,
                "raw_payload": row,
                "source_row_hash": row_hash("utility", row),
                "source_reference": f"{account}-{meter}-{period_start}-{period_end}" or f"row-{idx}",
                "parse_ok": parse_ok,
                "validation_flags": flags,
                "validation_message": "; ".join(flags),
            }
        )

    return parsed
