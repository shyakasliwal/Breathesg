from rest_framework.permissions import BasePermission

from .models import OrganizationMembership


class HasOrganizationAccess(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        org_id = getattr(obj, "organization_id", None)
        if org_id is None and hasattr(obj, "organization"):
            org_id = obj.organization_id
        return OrganizationMembership.objects.filter(user=request.user, organization_id=org_id).exists()
