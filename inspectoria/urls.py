from django.contrib import admin
from django.urls import path, include

handler404 = "core.views.error_404"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
]
