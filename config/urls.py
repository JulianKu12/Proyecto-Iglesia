from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template


def solo_superusuarios(request):
    return request.user.is_active and request.user.is_superuser


admin.site.has_permission = solo_superusuarios


def vista_error_preview(request, codigo):
    if codigo == 500:
        return HttpResponse(get_template("500.html").render({}), status=500)
    return render(request, f"{codigo}.html", status=codigo)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("cuentas/", include("accounts.urls")),
    path("miembros/", include("members.urls")),
    path("institucion/", include("institution.urls")),
    path("ministerios/", include("ministries.urls")),
    path("eventos/", include("events.urls")),
    path("asistencia/", include("attendance.urls")),
    path("finanzas/", include("finance.urls")),
    path("anuncios/", include("announcements.urls")),
    path("reportes/", include("reports.urls")),
]

handler403 = "core.permissions.permission_denied"
handler400 = "core.permissions.bad_request"
handler404 = "core.permissions.page_not_found"
handler500 = "core.permissions.server_error"
handler405 = "core.permissions.method_not_allowed"

if settings.DEBUG:
    urlpatterns += [
        path("_errores/400/", vista_error_preview, {"codigo": 400}, name="preview_400"),
        path("_errores/403/", vista_error_preview, {"codigo": 403}, name="preview_403"),
        path("_errores/404/", vista_error_preview, {"codigo": 404}, name="preview_404"),
        path("_errores/500/", vista_error_preview, {"codigo": 500}, name="preview_500"),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
