from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum

from .models import Aportacion


def rango_mes(anio, mes):
    return date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1])


def mes_anterior(anio, mes):
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


def mes_siguiente(anio, mes):
    return (anio + 1, 1) if mes == 12 else (anio, mes + 1)


def resumen_mensual(anio, mes):
    inicio, fin = rango_mes(anio, mes)
    vigentes = Aportacion.objects.filter(anulada=False, fecha__range=(inicio, fin))
    agregado = vigentes.aggregate(total=Sum("monto"), cantidad=Count("id"))
    total = agregado["total"] or Decimal("0.00")
    cantidad = agregado["cantidad"] or 0
    por_concepto = list(vigentes.values("concepto").annotate(total=Sum("monto"), cantidad=Count("id")))
    por_metodo = list(vigentes.values("metodo").annotate(total=Sum("monto"), cantidad=Count("id")))
    anonimas = vigentes.filter(miembro__isnull=True).aggregate(total=Sum("monto"), cantidad=Count("id"))
    anterior_anio, anterior_mes = mes_anterior(anio, mes)
    anterior_inicio, anterior_fin = rango_mes(anterior_anio, anterior_mes)
    anterior = Aportacion.objects.filter(anulada=False, fecha__range=(anterior_inicio, anterior_fin)).aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
    diferencia = total - anterior
    porcentaje = (diferencia * 100 / anterior).quantize(Decimal("0.01")) if anterior else None
    return {
        "total": total,
        "cantidad": cantidad,
        "por_concepto": por_concepto,
        "por_metodo": por_metodo,
        "anonimas": anonimas["cantidad"] or 0,
        "anonimas_total": anonimas["total"] or Decimal("0.00"),
        "promedio": (total / cantidad).quantize(Decimal("0.01")) if cantidad else Decimal("0.00"),
        "anterior": anterior,
        "diferencia": diferencia,
        "porcentaje": porcentaje,
    }


def resumen_periodo(inicio, fin):
    queryset = Aportacion.objects.filter(anulada=False, fecha__range=(inicio, fin))
    agregado = queryset.aggregate(total=Sum("monto"), cantidad=Count("id"))
    return {"total": agregado["total"] or Decimal("0.00"), "cantidad": agregado["cantidad"] or 0}
