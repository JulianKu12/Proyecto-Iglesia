from django import forms

from .models import Anuncio


class AnuncioForm(forms.ModelForm):
    class Meta:
        model = Anuncio
        fields = ("titulo", "contenido", "fecha_publicacion", "vigente_hasta", "importante")
        widgets = {
            "contenido": forms.Textarea(attrs={"rows": 6}),
            "fecha_publicacion": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "vigente_hasta": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("vigente_hasta") and cleaned.get("fecha_publicacion") and cleaned["vigente_hasta"] < cleaned["fecha_publicacion"]:
            self.add_error("vigente_hasta", "La vigencia no puede terminar antes de la publicación.")
        return cleaned
