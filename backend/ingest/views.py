from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivityRecord, AuditEvent, DataSource, IngestionBatch, OrganizationMembership
from .serializers import (
    ActivityRecordSerializer,
    AuditEventSerializer,
    DataSourceSerializer,
    IngestionBatchSerializer,
    LoginSerializer,
    OrganizationSerializer,
    ReviewActionSerializer,
)
from .services import ingest_uploaded_file, review_record


def _membership(user):
    return (
        OrganizationMembership.objects.select_related("organization")
        .filter(user=user)
        .first()
    )


class MeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization membership"}, status=403)
        return Response(
            {
                "user": {"id": request.user.id, "email": request.user.email},
                "organization": OrganizationSerializer(membership.organization).data,
                "role": membership.role,
            }
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response({"detail": "Invalid credentials"}, status=400)
        login(request, user)
        membership = _membership(user)
        return Response(
            {
                "user": {"id": user.id, "email": user.email},
                "organization": OrganizationSerializer(membership.organization).data
                if membership
                else None,
            }
        )


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"ok": True})


class DashboardView(APIView):
    def get(self, request):
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization"}, status=403)
        org = membership.organization
        qs = ActivityRecord.objects.filter(organization=org)
        return Response(
            {
                "totals": {
                    "records": qs.count(),
                    "failed": qs.filter(parse_ok=False).count(),
                    "suspicious": qs.filter(~Q(validation_flags=[])).count(),
                    "pending_review": qs.filter(review_status=ActivityRecord.ReviewStatus.PENDING).count(),
                    "approved_locked": qs.filter(is_locked_for_audit=True).count(),
                },
                "by_scope": list(qs.values("scope").annotate(count=Count("id")).order_by("scope")),
                "by_source": list(
                    qs.values("source__source_type").annotate(count=Count("id")).order_by("source__source_type")
                ),
                "recent_batches": IngestionBatchSerializer(
                    IngestionBatch.objects.filter(organization=org).order_by("-created_at")[:5],
                    many=True,
                ).data,
            }
        )


class DataSourceListView(APIView):
    def get(self, request):
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization"}, status=403)
        sources = DataSource.objects.filter(organization=membership.organization, is_active=True)
        return Response(DataSourceSerializer(sources, many=True).data)


class IngestUploadView(APIView):
    def post(self, request, source_type: str):
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization"}, status=403)

        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "file is required"}, status=400)

        try:
            source = DataSource.objects.get(
                organization=membership.organization, source_type=source_type
            )
        except DataSource.DoesNotExist:
            return Response({"detail": "Unknown source"}, status=404)

        batch = ingest_uploaded_file(
            organization=membership.organization,
            source=source,
            uploaded_file=upload,
            user=request.user,
        )
        return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class ActivityRecordListView(APIView):
    def get(self, request):
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization"}, status=403)

        qs = ActivityRecord.objects.filter(organization=membership.organization).select_related("source")

        status_filter = request.query_params.get("review_status")
        if status_filter:
            qs = qs.filter(review_status=status_filter)

        if request.query_params.get("failed") == "true":
            qs = qs.filter(parse_ok=False)
        if request.query_params.get("suspicious") == "true":
            qs = qs.exclude(validation_flags=[])

        source_type = request.query_params.get("source_type")
        if source_type:
            qs = qs.filter(source__source_type=source_type)

        serializer = ActivityRecordSerializer(qs.order_by("-created_at")[:500], many=True)
        return Response(serializer.data)


class ActivityReviewView(APIView):
    def post(self, request, record_id: int):
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization"}, status=403)

        try:
            record = ActivityRecord.objects.get(id=record_id, organization=membership.organization)
        except ActivityRecord.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated = review_record(
                record=record,
                user=request.user,
                action=serializer.validated_data["action"],
                note=serializer.validated_data.get("note", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(ActivityRecordSerializer(updated).data)


class AuditTrailView(APIView):
    def get(self, request):
        membership = _membership(request.user)
        if not membership:
            return Response({"detail": "No organization"}, status=403)
        events = AuditEvent.objects.filter(organization=membership.organization).order_by("-created_at")[:100]
        return Response(AuditEventSerializer(events, many=True).data)
