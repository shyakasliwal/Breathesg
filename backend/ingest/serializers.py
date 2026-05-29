from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ActivityRecord, AuditEvent, DataSource, IngestionBatch, Organization

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug")


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ("id", "source_type", "display_name", "is_active")


class IngestionBatchSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(source="source.source_type", read_only=True)

    class Meta:
        model = IngestionBatch
        fields = (
            "id",
            "source_type",
            "original_filename",
            "status",
            "row_count",
            "success_count",
            "error_count",
            "warning_count",
            "error_summary",
            "created_at",
        )


class ActivityRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(source="source.source_type", read_only=True)
    suspicious = serializers.SerializerMethodField()

    class Meta:
        model = ActivityRecord
        fields = (
            "id",
            "source_type",
            "scope",
            "category",
            "activity_date",
            "period_start",
            "period_end",
            "facility_code",
            "vendor_or_carrier",
            "description",
            "quantity",
            "unit",
            "normalized_quantity",
            "normalized_unit",
            "spend_amount",
            "spend_currency",
            "origin",
            "destination",
            "distance_km",
            "parse_ok",
            "validation_flags",
            "validation_message",
            "review_status",
            "is_locked_for_audit",
            "source_reference",
            "suspicious",
            "created_at",
        )

    def get_suspicious(self, obj) -> bool:
        return bool(obj.validation_flags)


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ("id", "action", "actor_email", "note", "before_state", "after_state", "created_at")


class ReviewActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    note = serializers.CharField(required=False, allow_blank=True, default="")


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
