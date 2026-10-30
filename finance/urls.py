from django.urls import path

from .views import (
    AportacionAnularView,
    AportacionCreateView,
    AportacionDetailView,
    AportacionUpdateView,
    AportacionesListView,
    IngresosPeriodoView,
    ResumenFinanzasView,
)

urlpatterns = [
    path("", AportacionesListView.as_view(), name="aportaciones"),
    path("nueva/", AportacionCreateView.as_view(), name="aportacion_crear"),
    path("resumen/", ResumenFinanzasView.as_view(), name="finanzas_resumen"),
    path("periodo/", IngresosPeriodoView.as_view(), name="finanzas_periodo"),
    path("<int:pk>/", AportacionDetailView.as_view(), name="aportacion_detalle"),
    path("<int:pk>/editar/", AportacionUpdateView.as_view(), name="aportacion_editar"),
    path("<int:pk>/anular/", AportacionAnularView.as_view(), name="aportacion_anular"),
]
