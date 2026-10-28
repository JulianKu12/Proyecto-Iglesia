from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from .permissions import ROL_ADMINISTRADOR, RoleRequiredMixin


class InicioView(LoginRequiredMixin, View):
    template_name = "core/inicio.html"

    def get(self, request):
        return render(request, self.template_name)


class UsuariosView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def get(self, request):
        return HttpResponse("Gestión de usuarios")


def inicio(request):
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    return render(request, "core/inicio.html")
