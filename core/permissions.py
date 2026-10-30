from django.core.exceptions import PermissionDenied
from django.shortcuts import render


ROL_ADMINISTRADOR = "Administrador"
ROL_PASTOR = "Pastor"
ROL_SECRETARIO = "Secretario"
ROL_TESORERO = "Tesorero"
ROL_COORDINADOR = "Coordinador"
ROLES = (
    ROL_ADMINISTRADOR,
    ROL_PASTOR,
    ROL_SECRETARIO,
    ROL_TESORERO,
    ROL_COORDINADOR,
)


class RoleRequiredMixin:
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.groups.filter(name__in=self.allowed_roles).exists():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(self.request.get_full_path())


def permission_denied(request, exception=None):
    return render(request, "403.html", status=403)


def bad_request(request, exception=None):
    return render(request, "400.html", status=400)


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)


def method_not_allowed(request, exception=None):
    return render(request, "405.html", status=405)
