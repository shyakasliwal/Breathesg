from django.contrib import admin

from .models import ActivityRecord, AuditEvent, DataSource, IngestionBatch, Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role")


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("organization", "source_type", "display_name", "is_active")


@admin.register(IngestionBatch)
class IngestionBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "organization", "source", "status", "row_count", "created_at")


@admin.register(ActivityRecord)
class ActivityRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "scope",
        "category",
        "parse_ok",
        "review_status",
        "is_locked_for_audit",
    )
    list_filter = ("scope", "category", "review_status", "parse_ok")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("organization", "action", "actor", "created_at")
