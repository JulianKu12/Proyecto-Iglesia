from datetime import date, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from events.models import Evento

from .models import Asistencia


def porcentajes(presentes, total):
    return round(presentes * 100 / total, 2) if total else 0


def resumen_evento(evento):
    total = evento.asistencias.count()
    presentes = evento.asistencias.filter(presente=True).count()
    return {
        "evento_id": evento.pk,
        "titulo": evento.titulo,
        "fecha": evento.fecha,
        "hora": evento.hora,
        "tipo": evento.get_tipo_display(),
        "ministerio": str(evento.ministerio) if evento.ministerio else "",
        "presentes": presentes,
        "ausentes": total - presentes,
        "total": total,
        "porcentaje": porcentajes(presentes, total),
    }


def semana_de(fecha):
    inicio = fecha - timedelta(days=fecha.weekday())
    return inicio, inicio + timedelta(days=6)


def rango_mes(fecha):
    inicio = fecha.replace(day=1)
    siguiente = (inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
    return inicio, siguiente - timedelta(days=1)


def resumen_periodo(inicio, fin, ministerio_id="", tipo=""):
    eventos = Evento.objects.select_related("ministerio").filter(
        fecha__range=(inicio, fin),
        asistencias__isnull=False,
    ).annotate(
        total_asistencias=Count("asistencias"),
        presentes_asistencias=Count("asistencias", filter=Q(asistencias__presente=True)),
    ).distinct()
    if ministerio_id:
        eventos = eventos.filter(ministerio_id=ministerio_id)
    if tipo:
        eventos = eventos.filter(tipo=tipo)
    filas = []
    for evento in eventos.order_by("fecha", "hora", "titulo"):
        presentes = evento.presentes_asistencias
        total = evento.total_asistencias
        filas.append(
            {
                "evento_id": evento.pk,
                "titulo": evento.titulo,
                "fecha": evento.fecha,
                "hora": evento.hora,
                "tipo": evento.get_tipo_display(),
                "ministerio": str(evento.ministerio) if evento.ministerio else "",
                "presentes": presentes,
                "ausentes": total - presentes,
                "total": total,
                "porcentaje": porcentajes(presentes, total),
            }
        )
    total_presentes = sum(fila["presentes"] for fila in filas)
    total_ausentes = sum(fila["ausentes"] for fila in filas)
    total = total_presentes + total_ausentes
    return {
        "filas": filas,
        "total_presentes": total_presentes,
        "total_ausentes": total_ausentes,
        "total": total,
        "porcentaje": porcentajes(total_presentes, total),
        "promedio": round(total_presentes / len(filas), 2) if filas else 0,
    }
