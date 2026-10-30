from datetime import date
from django.db.models import Count, Q
from attendance.services import resumen_periodo
from events.models import Evento
from finance.services import resumen_periodo as resumen_finanzas
from members.models import Miembro
from ministries.models import Ministerio
from finance.models import Aportacion


def miembros_report(filters, usuario):
    qs = Miembro.objects.prefetch_related("ministerios").all()
    if filters.get("estado", "activos") != "todos":
        qs = qs.filter(activo=filters.get("estado", "activos") == "activos")
    if filters.get("busqueda"):
        qs = qs.filter(nombre_completo__icontains=filters["busqueda"])
    if filters.get("desde"):
        qs = qs.filter(fecha_ingreso__gte=filters["desde"])
    if filters.get("hasta"):
        qs = qs.filter(fecha_ingreso__lte=filters["hasta"])
    filas = [{"nombre": m.nombre_completo, "telefono": m.telefono, "correo": m.correo,
              "fecha": m.fecha_ingreso, "estado": "Activo" if m.activo else "Inactivo",
              "ministerios": ", ".join(x.nombre for x in m.ministerios.all())} for m in qs]
    return filas, ["Nombre", "Teléfono", "Correo", "Fecha de ingreso", "Estado", "Ministerios"]


def asistencia_report(filters, usuario):
    inicio = filters.get("desde") or date(1900, 1, 1)
    fin = filters.get("hasta") or date(2999, 12, 31)
    data = resumen_periodo(inicio, fin, filters.get("ministerio", ""), filters.get("tipo", ""))
    filas = data["filas"]
    if usuario.groups.filter(name="Coordinador").exists():
        filas = [f for f in filas if Evento.objects.filter(pk=f["evento_id"], ministerio__coordinador=usuario).exists()]
    if filters.get("evento"):
        filas = [f for f in filas if str(f["evento_id"]) == filters["evento"]]
    return filas, ["Fecha", "Título", "Tipo", "Ministerio", "Presentes", "Ausentes", "Total", "%"]


def ministerios_report(filters, usuario):
    qs = Ministerio.objects.filter(activo=True).prefetch_related("miembros")
    if usuario.groups.filter(name="Coordinador").exists():
        qs = qs.filter(coordinador=usuario)
    filas = []
    for m in qs:
        eventos = Evento.objects.filter(ministerio=m, fecha__range=(filters.get("desde") or date(1900,1,1), filters.get("hasta") or date(2999,12,31)), asistencias__isnull=False)
        total = sum(e.asistencias.count() for e in eventos)
        presentes = sum(e.asistencias.filter(presente=True).count() for e in eventos)
        filas.append({"ministerio": m.nombre, "coordinador": str(m.coordinador or ""), "integrantes": m.miembros.filter(activo=True).count(), "eventos": eventos.count(), "registros": total, "presentes": presentes, "porcentaje": round(presentes*100/total, 2) if total else 0})
    return filas, ["Ministerio", "Coordinador", "Integrantes activos", "Eventos", "Registros", "Presentes", "%"]


def ingresos_report(filters, usuario):
    qs = Aportacion.objects.filter(fecha__range=(filters["desde"], filters["hasta"]))
    if not filters.get("anuladas"):
        qs = qs.filter(anulada=False)
    filas = [{"fecha": a.fecha, "concepto": a.get_concepto_display(), "metodo": a.get_metodo_display(),
              "miembro": str(a.miembro or "Anónimo"), "monto": a.monto,
              "estado": "Anulada" if a.anulada else "Vigente"} for a in qs]
    return filas, ["Fecha", "Concepto", "Método", "Miembro", "Monto", "Estado"]
