from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from core.permissions import ROLES
from .models import Usuario
from members.models import Miembro


class BootstrapErrorsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._errores_marcados = False

    def full_clean(self):
        super().full_clean()
        if not self._errores_marcados:
            for name, field in self.fields.items():
                if self.errors.get(name):
                    css = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = f"{css} is-invalid".strip()
            self._errores_marcados = True


class UsuarioCreationForm(BootstrapErrorsMixin, forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(render_value=False))
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(render_value=False))
    rol = forms.ChoiceField(choices=[(rol, rol) for rol in ROLES], label="Rol")

    class Meta:
        model = Usuario
        fields = ("correo", "nombre", "activo", "miembro")

    miembro = forms.ModelChoiceField(queryset=Miembro.objects.all(), required=False, label="Miembro vinculado")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if password1:
            try:
                password_validation.validate_password(password1)
            except forms.ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password1"])
        if commit:
            usuario.save()
            self._guardar_rol(usuario)
        return usuario

    def _guardar_rol(self, usuario):
        from django.contrib.auth.models import Group
        usuario.groups.set([Group.objects.get(name=self.cleaned_data["rol"])])


class UsuarioUpdateForm(BootstrapErrorsMixin, forms.ModelForm):
    rol = forms.ChoiceField(choices=[(rol, rol) for rol in ROLES], label="Rol")

    class Meta:
        model = Usuario
        fields = ("correo", "nombre", "activo", "rol", "miembro")

    miembro = forms.ModelChoiceField(queryset=Miembro.objects.all(), required=False, label="Miembro vinculado")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["rol"] = self.instance.groups.values_list("name", flat=True).first()

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and self.instance == getattr(self, "request_user", None):
            rol_actual = self.instance.groups.values_list("name", flat=True).first()
            if cleaned_data.get("rol") != rol_actual:
                self.add_error("rol", "No puedes cambiar tu propio rol.")
            if not cleaned_data.get("activo"):
                self.add_error("activo", "No puedes desactivarte a ti mismo.")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        from django.contrib.auth.models import Group
        usuario.groups.set([Group.objects.get(name=self.cleaned_data["rol"])])
        return usuario


class CorreoPasswordResetForm(BootstrapErrorsMixin, PasswordResetForm):
    email = forms.EmailField(label="Correo", max_length=254)

    def get_users(self, email):
        for user in Usuario._default_manager.filter(correo__iexact=email, activo=True):
            if user.has_usable_password():
                yield user


class EspanolSetPasswordForm(BootstrapErrorsMixin, SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        password_validation.validate_password(password, self.user)
        return password
