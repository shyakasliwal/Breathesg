from django.urls import path

from . import views

urlpatterns = [
    path("auth/csrf/", views.CsrfView.as_view(), name="csrf"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("sources/", views.DataSourceListView.as_view(), name="sources"),
    path("ingest/<str:source_type>/", views.IngestUploadView.as_view(), name="ingest"),
    path("records/", views.ActivityRecordListView.as_view(), name="records"),
    path("records/<int:record_id>/review/", views.ActivityReviewView.as_view(), name="record-review"),
    path("audit/", views.AuditTrailView.as_view(), name="audit"),
]
