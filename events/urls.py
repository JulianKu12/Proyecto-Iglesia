from django.urls import path

from .views import (
    CalendarioDatosView,
    CalendarioView,
    EventoCancelarView,
    EventoCreateView,
    EventoDetailView,
    EventoReactivarView,
    EventoUpdateView,
    EventosListView,
)

urlpatterns = [
    path("", EventosListView.as_view(), name="eventos"),
    path("nuevo/", EventoCreateView.as_view(), name="evento_crear"),
    path("calendario/", CalendarioView.as_view(), name="calendario"),
    path("calendario/datos/", CalendarioDatosView.as_view(), name="calendario_datos"),
    path("<int:pk>/", EventoDetailView.as_view(), name="evento_detalle"),
    path("<int:pk>/editar/", EventoUpdateView.as_view(), name="evento_editar"),
    path("<int:pk>/cancelar/", EventoCancelarView.as_view(), name="evento_cancelar"),
    path("<int:pk>/reactivar/", EventoReactivarView.as_view(), name="evento_reactivar"),
]
