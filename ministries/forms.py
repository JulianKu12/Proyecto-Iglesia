from django import forms

from accounts.models import Usuario
from core.permissions import ROL_COORDINADOR
from members.models import Miembro

from .models import Ministerio


class MinisterioForm(forms.ModelForm):
    class Meta:
        model = Ministerio
        fields = ("nombre", "descripcion", "coordinador", "activo")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["coordinador"].queryset = Usuario.objects.filter(
            activo=True, groups__name=ROL_COORDINADOR
        ).distinct()

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        nombres_existentes = Ministerio.objects.exclude(pk=self.instance.pk).values_list("nombre", flat=True)
        if any(nombre_existente.casefold() == nombre.casefold() for nombre_existente in nombres_existentes):
            raise forms.ValidationError("Ya existe un ministerio con ese nombre.")
        return nombre


class AgregarIntegrantesForm(forms.Form):
    miembros = forms.ModelMultipleChoiceField(
        queryset=Miembro.objects.filter(activo=True),
        required=True,
        label="Miembros",
        widget=forms.SelectMultiple(attrs={"size": 8}),
    )

    def __init__(self, *args, ministerio=None, **kwargs):
        super().__init__(*args, **kwargs)
        if ministerio is not None:
            self.fields["miembros"].queryset = Miembro.objects.filter(
                activo=True
            ).exclude(ministerios=ministerio)
