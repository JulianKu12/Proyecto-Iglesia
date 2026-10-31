from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.urls import reverse
from django.utils.crypto import salted_hmac
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View

from core.permissions import ROL_ADMINISTRADOR, RoleRequiredMixin
from .forms import CorreoPasswordResetForm, EspanolSetPasswordForm, UsuarioCreationForm, UsuarioUpdateForm
from .models import Usuario


def _administradores_activos():
    return Usuario.objects.filter(activo=True, groups__name="Administrador").distinct().count()


class CorreoLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def _clave_intentos(self):
        correo = self.request.POST.get("username", "").strip().lower()
        ip = self.request.META.get("REMOTE_ADDR", "")
        return "login-fallos:" + salted_hmac("login", f"{correo}|{ip}").hexdigest()

    def dispatch(self, request, *args, **kwargs):
        if cache.get(self._clave_intentos()):
            from django.contrib import messages
            messages.error(request, "Demasiados intentos fallidos. Intenta nuevamente en 10 minutos.")
            return self.get(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        clave = self._clave_intentos()
        fallos = cache.get(clave, 0) + 1
        if fallos >= 5:
            cache.set(clave, True, 600)
            form.add_error(None, "Demasiados intentos fallidos. Intenta nuevamente en 10 minutos.")
        else:
            cache.set(clave, fallos, 600)
            form.add_error(None, "El correo o la contraseña no son correctos.")
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(self._clave_intentos())
        return super().form_valid(form)

    def get_success_url(self):
        destino = self.get_redirect_url()
        if destino and url_has_allowed_host_and_scheme(
            destino,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return destino
        return reverse("inicio")


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
        form = UsuarioUpdateForm(instance=self.get_usuario(pk))
        form.request_user = request.user
        return render(request, "accounts/usuario_form.html", {"form": form})

    def post(self, request, pk):
        usuario = self.get_usuario(pk)
        era_coordinador = usuario.groups.filter(name="Coordinador").exists()
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        form.request_user = request.user
        if form.is_valid():
            rol_nuevo = form.cleaned_data["rol"]
            if usuario.activo and usuario.groups.filter(name="Administrador").exists() and (
                rol_nuevo != "Administrador" or not form.cleaned_data["activo"]
            ) and _administradores_activos() <= 1:
                form.add_error("rol", "Debe existir al menos un Administrador activo.")
            if not form.errors:
                form.save()
                if era_coordinador and (not usuario.activo or rol_nuevo != "Coordinador"):
                    from ministries.models import Ministerio
                    if Ministerio.objects.filter(coordinador=usuario).update(coordinador=None):
                        messages.warning(request, "Los ministerios del usuario quedaron sin coordinador.")
                messages.success(request, "Usuario actualizado correctamente.")
                return redirect("usuarios")
        return render(request, "accounts/usuario_form.html", {"form": form})


class UsuarioDeactivateView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        if usuario == request.user:
            messages.error(request, "No puedes desactivar tu propia cuenta.")
            return redirect("usuarios")
        if usuario.groups.filter(name="Administrador").exists() and usuario.activo and _administradores_activos() <= 1:
            messages.error(request, "Debe existir al menos un Administrador activo.")
            return redirect("usuarios")
        era_coordinador = usuario.groups.filter(name="Coordinador").exists()
        usuario.activo = False
        usuario.save(update_fields=("activo",))
        if era_coordinador:
            from ministries.models import Ministerio
            if Ministerio.objects.filter(coordinador=usuario).update(coordinador=None):
                messages.warning(request, "Los ministerios del usuario quedaron sin coordinador.")
        messages.success(request, "Usuario desactivado correctamente.")
        return redirect("usuarios")


class UsuarioReactivateView(RoleRequiredMixin, View):
    allowed_roles = (ROL_ADMINISTRADOR,)

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        usuario.activo = True
        usuario.save(update_fields=("activo",))
        messages.success(request, "Usuario reactivado correctamente.")
        return redirect("usuarios")


PasswordResetView = auth_views.PasswordResetView
PasswordResetConfirmView = auth_views.PasswordResetConfirmView
