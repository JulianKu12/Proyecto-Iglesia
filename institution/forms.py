from django import forms
from django.forms import inlineformset_factory

from .models import ConfiguracionIglesia, HorarioReunion


class ConfiguracionIglesiaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionIglesia
        fields = ("nombre", "logotipo", "direccion", "telefono", "correo_contacto")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def full_clean(self):
        super().full_clean()
        for name, field in self.fields.items():
            if self.errors.get(name):
                field.widget.attrs["class"] = "is-invalid"


HorarioReunionFormSet = inlineformset_factory(
    ConfiguracionIglesia,
    HorarioReunion,
    fields=("dia_semana", "hora", "nombre"),
    extra=1,
    can_delete=True,
    can_delete_extra=False,
    widgets={"hora": forms.TimeInput(attrs={"type": "time"})},
)
