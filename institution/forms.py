from django import forms
from django.forms import inlineformset_factory

from .models import ConfiguracionIglesia, HorarioReunion


class ConfiguracionIglesiaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionIglesia
        fields = ("nombre", "logotipo", "direccion", "telefono", "correo_contacto")


HorarioReunionFormSet = inlineformset_factory(
    ConfiguracionIglesia,
    HorarioReunion,
    fields=("dia_semana", "hora", "nombre"),
    extra=1,
    can_delete=True,
    widgets={"hora": forms.TimeInput(attrs={"type": "time"})},
)
