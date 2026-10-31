from django.urls import path
from .views import ReportesView

urlpatterns = [path("", ReportesView.as_view(), name="reportes")]
