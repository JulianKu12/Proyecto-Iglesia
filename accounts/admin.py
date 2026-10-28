from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    ordering = ("nombre",)
    list_display = ("correo", "nombre", "activo")
    list_filter = ("activo", "is_staff", "is_superuser", "groups")
    fieldsets = (
        (None, {"fields": ("correo", "password")}),
        ("Datos personales", {"fields": ("nombre", "activo")}),
        ("Permisos", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("correo", "nombre", "password1", "password2")}),
    )
    search_fields = ("correo", "nombre")
