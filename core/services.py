from datetime import timedelta

from django.utils import timezone

from attendance.models import Asistencia
from events.models import Evento
from finance.models import Aportacion
from finance.services import mes_anterior, resumen_mensual
from members.models import Miembro
from ministries.models import Ministerio

from .permissions import ROL_COORDINADOR, ROL_SECRETARIO, ROL_TESORERO, puede_ver_finanzas


def _rango_meses(cantidad):
    hoy = timezone.localdate()
    meses = []
    anio, mes = hoy.year, hoy.month
    for _ in range(cantidad):
        meses.append((anio, mes))
        anio, mes = mes_anterior(anio, mes)
    return list(reversed(meses))


def dashboard_data(usuario):
    hoy = timezone.localdate()
    coordinador = usuario.groups.filter(name=ROL_COORDINADOR).exists()
    eventos = Evento.objects.filter(fecha__range=(hoy, hoy + timedelta(days=30)), estado=Evento.ESTADO_PROGRAMADO)
    if coordinador:
        eventos = eventos.filter(ministerio__coordinador=usuario)
    eventos_proximos = list(eventos.select_related("ministerio").order_by("fecha", "hora")[:5])
    miembros = Miembro.objects.filter(activo=True)
    ministerios = Ministerio.objects.filter(activo=True)
    if coordinador:
        miembros = miembros.filter(ministerios__coordinador=usuario).distinct()
        ministerios = ministerios.filter(coordinador=usuario)
    mes_inicio = hoy.replace(day=1)
    presentes_mes = Asistencia.objects.filter(presente=True, evento__fecha__gte=mes_inicio, evento__fecha__lte=hoy)
    asistencia_eventos = Evento.objects.filter(asistencias__isnull=False)
    if coordinador:
        asistencia_eventos = asistencia_eventos.filter(ministerio__coordinador=usuario)
    asistencia_grafica = []
    for evento in asistencia_eventos.order_by("-fecha", "-hora")[:8][::-1]:
        asistencia_grafica.append({"label": evento.titulo, "value": evento.asistencias.filter(presente=True).count()})
    ingresos = ingresos_data = None
    if puede_ver_finanzas(usuario) and not usuario.groups.filter(name__in=(ROL_SECRETARIO, ROL_COORDINADOR)).exists():
        actual = resumen_mensual(hoy.year, hoy.month)
        anterior_anio, anterior_mes = mes_anterior(hoy.year, hoy.month)
        ingresos = actual
        ingresos_data = []
        for anio, mes in _rango_meses(6):
            ingresos_data.append({"label": f"{mes:02d}/{anio}", "value": float(resumen_mensual(anio, mes)["total"])})
    integrantes = [
        {"label": ministerio.nombre, "value": ministerio.miembros.filter(activo=True).count()}
        for ministerio in ministerios
    ]
    altas = []
    for anio, mes in _rango_meses(6):
        altas.append({"label": f"{mes:02d}/{anio}", "value": Miembro.objects.filter(fecha_ingreso__year=anio, fecha_ingreso__month=mes).count()})
    return {
        "miembros_activos": miembros.count(),
        "ministerios_activos": ministerios.count(),
        "eventos_proximos": eventos.count(),
        "proximos_eventos": eventos_proximos,
        "asistencia_mes": presentes_mes.filter(evento__in=asistencia_eventos).count(),
        "asistencia_total": Asistencia.objects.filter(presente=True, evento__in=asistencia_eventos).count(),
        "asistencia_grafica": asistencia_grafica,
        "integrantes_grafica": integrantes,
        "altas_grafica": altas,
        "ingresos": ingresos,
        "ingresos_grafica": ingresos_data,
    }
