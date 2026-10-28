from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View

from core.permissions import ROL_ADMINISTRADOR, RoleRequiredMixin
from .forms import CorreoPasswordResetForm, UsuarioCreationForm, UsuarioUpdateForm
from .models import Usuario


class CorreoLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class UsuariosListView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def get(self, request):
        return render(request, "accounts/usuarios_list.html", {"usuarios": Usuario.objects.all()})


class UsuarioCreateView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def get(self, request):
        return render(request, "accounts/usuario_form.html", {"form": UsuarioCreationForm()})

    def post(self, request):
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("usuarios")
        return render(request, "accounts/usuario_form.html", {"form": form})


class UsuarioUpdateView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def get_usuario(self, pk):
        return get_object_or_404(Usuario, pk=pk)

    def get(self, request, pk):
        return render(request, "accounts/usuario_form.html", {"form": UsuarioUpdateForm(instance=self.get_usuario(pk))})

    def post(self, request, pk):
        usuario = self.get_usuario(pk)
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente.")
            return redirect("usuarios")
        return render(request, "accounts/usuario_form.html", {"form": form})


class UsuarioDeactivateView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        usuario.activo = False
        usuario.save(update_fields=("activo",))
        messages.success(request, "Usuario desactivado correctamente.")
        return redirect("usuarios")


PasswordResetView = auth_views.PasswordResetView
