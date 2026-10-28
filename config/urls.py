from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("cuentas/", include("accounts.urls")),
]

handler403 = "core.permissions.permission_denied"
