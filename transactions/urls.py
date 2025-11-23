from django.urls import path
from .views import portfolio_view

urlpatterns = [
    path("reports/portfolio/", portfolio_view, name="portfolio"),
]
