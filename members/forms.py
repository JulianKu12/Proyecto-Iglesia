from django import forms
from django.utils import timezone

from .models import Miembro


class MiembroForm(forms.ModelForm):
    class Meta:
        model = Miembro
        fields = ("nombre_completo", "telefono", "correo", "fecha_ingreso", "activo")
        widgets = {"fecha_ingreso": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial["fecha_ingreso"] = timezone.localdate()
