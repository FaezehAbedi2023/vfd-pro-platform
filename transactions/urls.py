from django.urls import path
from .views import portfolio_view, download_vfd_report

urlpatterns = [
    path("reports/portfolio/", portfolio_view, name="portfolio"),
    path("download-vfd/", download_vfd_report, name="download_vfd"),
]
