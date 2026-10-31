from django import forms
from django.utils import timezone

from .models import Miembro


class MiembroForm(forms.ModelForm):
    class Meta:
        model = Miembro
        fields = ("nombre_completo", "telefono", "correo", "fecha_ingreso", "activo")
        widgets = {"fecha_ingreso": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def full_clean(self):
        super().full_clean()
        for name, field in self.fields.items():
            if self.errors.get(name):
                field.widget.attrs["class"] = "is-invalid"
        if not self.instance.pk:
            self.initial["fecha_ingreso"] = timezone.localdate()
