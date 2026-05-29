from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        ANALYST = "analyst", "Analyst"
        ADMIN = "admin", "Admin"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)

    class Meta:
        unique_together = ("user", "organization")


class DataSource(models.Model):
    class SourceType(models.TextChoices):
        SAP = "sap", "SAP (fuel & procurement)"
        UTILITY = "utility", "Utility electricity"
        TRAVEL = "travel", "Corporate travel"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sources")
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    display_name = models.CharField(max_length=200)
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("organization", "source_type")


class IngestionBatch(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    row_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ActivityRecord(models.Model):
    class Scope(models.TextChoices):
        SCOPE_1 = "scope_1", "Scope 1"
        SCOPE_2 = "scope_2", "Scope 2"
        SCOPE_3 = "scope_3", "Scope 3"

    class Category(models.TextChoices):
        FUEL = "fuel", "Fuel"
        PROCUREMENT = "procurement", "Procurement"
        ELECTRICITY = "electricity", "Electricity"
        FLIGHT = "flight", "Flight"
        HOTEL = "hotel", "Hotel"
        GROUND = "ground", "Ground transport"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="activities")
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="records")
    source = models.ForeignKey(DataSource, on_delete=models.PROTECT)

    scope = models.CharField(max_length=20, choices=Scope.choices)
    category = models.CharField(max_length=30, choices=Category.choices)

    activity_date = models.DateField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    facility_code = models.CharField(max_length=64, blank=True)
    vendor_or_carrier = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    unit = models.CharField(max_length=32, blank=True)
    normalized_quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    normalized_unit = models.CharField(max_length=32, blank=True)

    spend_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    spend_currency = models.CharField(max_length=8, blank=True)

    origin = models.CharField(max_length=64, blank=True)
    destination = models.CharField(max_length=64, blank=True)
    distance_km = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)

    raw_payload = models.JSONField()
    source_row_hash = models.CharField(max_length=64, db_index=True)
    source_reference = models.CharField(max_length=128, blank=True)

    parse_ok = models.BooleanField(default=True)
    validation_flags = models.JSONField(default=list, blank=True)
    validation_message = models.TextField(blank=True)

    review_status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_activities",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_locked_for_audit = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "review_status"]),
            models.Index(fields=["organization", "scope"]),
            models.Index(fields=["organization", "parse_ok"]),
        ]


class AuditEvent(models.Model):
    class Action(models.TextChoices):
        INGEST = "ingest", "Ingest"
        EDIT = "edit", "Edit"
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        LOCK = "lock", "Lock for audit"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    record = models.ForeignKey(
        ActivityRecord, on_delete=models.CASCADE, null=True, blank=True, related_name="audit_events"
    )
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
