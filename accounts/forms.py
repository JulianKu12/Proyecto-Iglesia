from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm

from core.permissions import ROLES
from .models import Usuario
from members.models import Miembro


class UsuarioCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
    rol = forms.ChoiceField(choices=[(rol, rol) for rol in ROLES], label="Rol")

    class Meta:
        model = Usuario
        fields = ("correo", "nombre", "activo", "miembro")

    miembro = forms.ModelChoiceField(queryset=Miembro.objects.all(), required=False, label="Miembro vinculado")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Las contraseñas no coinciden.")
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


class UsuarioUpdateForm(forms.ModelForm):
    rol = forms.ChoiceField(choices=[(rol, rol) for rol in ROLES], label="Rol")

    class Meta:
        model = Usuario
        fields = ("correo", "nombre", "activo", "rol", "miembro")

    miembro = forms.ModelChoiceField(queryset=Miembro.objects.all(), required=False, label="Miembro vinculado")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["rol"] = self.instance.groups.values_list("name", flat=True).first()

    def save(self, commit=True):
        usuario = super().save(commit=commit)
        from django.contrib.auth.models import Group
        usuario.groups.set([Group.objects.get(name=self.cleaned_data["rol"])])
        return usuario


class CorreoPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Correo", max_length=254)
