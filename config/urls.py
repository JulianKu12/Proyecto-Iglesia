from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


def solo_superusuarios(request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = solo_superusuarios


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("cuentas/", include("accounts.urls")),
    path("miembros/", include("members.urls")),
    path("institucion/", include("institution.urls")),
]

handler403 = "core.permissions.permission_denied"
handler400 = "core.permissions.bad_request"
handler404 = "core.permissions.page_not_found"
handler500 = "core.permissions.server_error"
handler405 = "core.permissions.method_not_allowed"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
