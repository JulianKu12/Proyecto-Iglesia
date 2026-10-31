from django.urls import path

from .views import InstitucionUpdateView

urlpatterns = [path("", InstitucionUpdateView.as_view(), name="institucion")]
