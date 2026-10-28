from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("cuentas/", include("accounts.urls")),
    path("miembros/", include("members.urls")),
    path("institucion/", include("institution.urls")),
]

handler403 = "core.permissions.permission_denied"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
