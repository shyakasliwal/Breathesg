from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"status": "ok", "api_base": "/api/"})


urlpatterns = [
    path("", health),
    path("admin/", admin.site.urls),
    path("api/", include("ingest.urls")),
]
