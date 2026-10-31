from django.urls import path

from .views import (
    DetalleAsistenciaView,
    HistorialAsistenciaView,
    MiembroAsistenciaView,
    RegistrarAsistenciaView,
    ResumenAsistenciaView,
)

urlpatterns = [
    path("registrar/", RegistrarAsistenciaView.as_view(), name="asistencia_registrar"),
    path("historial/", HistorialAsistenciaView.as_view(), name="asistencia_historial"),
    path("evento/<int:pk>/", DetalleAsistenciaView.as_view(), name="asistencia_detalle"),
    path("resumen/", ResumenAsistenciaView.as_view(), name="asistencia_resumen"),
    path("miembro/<int:pk>/", MiembroAsistenciaView.as_view(), name="asistencia_miembro"),
]
