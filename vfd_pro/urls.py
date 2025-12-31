from django.urls import path, include

urlpatterns = [
    # path("reports/", include("vfd_pro.reports.caam.urls")),
    path("", include(("vfd_pro.reports.caam.urls", "caam"), namespace="caam"))
]
