from django.contrib.auth.views import (
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
)
from django.urls import path

from .views import (
    CorreoLoginView,
    UsuarioCreateView,
    UsuarioDeactivateView,
    UsuarioUpdateView,
    UsuariosListView,
)
from .forms import CorreoPasswordResetForm
from django.contrib.auth.views import PasswordResetView

urlpatterns = [
    path("login/", CorreoLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("usuarios/", UsuariosListView.as_view(), name="usuarios"),
    path("usuarios/nuevo/", UsuarioCreateView.as_view(), name="usuario_crear"),
    path("usuarios/<int:pk>/editar/", UsuarioUpdateView.as_view(), name="usuario_editar"),
    path("usuarios/<int:pk>/desactivar/", UsuarioDeactivateView.as_view(), name="usuario_desactivar"),
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            form_class=CorreoPasswordResetForm,
            success_url="/cuentas/password-reset/enviado/",
        ),
        name="password_reset",
    ),
    path("password-reset/enviado/", PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset/completo/", PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
]
