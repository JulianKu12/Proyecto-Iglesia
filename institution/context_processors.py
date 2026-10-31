from .models import ConfiguracionIglesia


def iglesia(request):
    configuracion = ConfiguracionIglesia.objects.first()
    return {
        "configuracion_iglesia": configuracion,
        "nombre_iglesia": configuracion.nombre if configuracion else "Iglesia",
    }
