from django.urls import path

from .views import (
    MiembroCreateView,
    MiembroDetailView,
    MiembroEstadoView,
    MiembroUpdateView,
    MiembrosListView,
)

urlpatterns = [
    path("", MiembrosListView.as_view(), name="miembros"),
    path("nuevo/", MiembroCreateView.as_view(), name="miembro_crear"),
    path("<int:pk>/", MiembroDetailView.as_view(), name="miembro_detalle"),
    path("<int:pk>/editar/", MiembroUpdateView.as_view(), name="miembro_editar"),
    path("<int:pk>/estado/", MiembroEstadoView.as_view(), name="miembro_estado"),
]
