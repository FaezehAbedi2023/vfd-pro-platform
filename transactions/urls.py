from django.urls import path
from .views import portfolio_view, download_vfd_report
from . import views

urlpatterns = [
    path("reports/portfolio/", portfolio_view, name="portfolio"),
    path("download-vfd/", download_vfd_report, name="download_vfd"),
    path("clients/<int:client_id>/summary/",views.client_summary,name="client_summary" ),

    path(
    "client/<int:client_id>/ajax/revenue-criteria/",
    views.ajax_revenue_criteria,
    name="ajax_revenue_criteria",),

    path(
    "client/<int:client_id>/ajax/gm-criteria/",
    views.ajax_gm_criteria,
    name="ajax_gm_criteria",),

    path(
    "client/<int:client_id>/ajax/overhead-criteria/",
    views.ajax_oh_val_criteria,
    name="ajax_oh_val_criteria",),

    path(
    "client/<int:client_id>/ajax/overhead-pct-criteria/",
    views.ajax_oh_pct_criteria,
    name="ajax_oh_pct_criteria",),

    path(
    "client/<int:client_id>/ajax/ebitda-criteria/",
    views.ajax_ebitda_criteria,
    name="ajax_ebitda_criteria",),

    path(
    "client/<int:client_id>/ajax/newcust-criteria/",
    views.ajax_newcust_criteria,
    name="ajax_newcust_criteria",),

    path(
    "client/<int:client_id>/ajax/retention-criteria/",
    views.ajax_retention_criteria,
    name="ajax_retention_criteria",),

    path(
    "client/<int:client_id>/ajax/cash-criteria/",
    views.ajax_cash_criteria,
    name="ajax_cash_criteria",),

    path(
    "client/<int:client_id>/ajax/debtordays-criteria/",
    views.ajax_debtordays_criteria,
    name="ajax_debtordays_criteria",),

    path(
    "client/<int:client_id>/ajax/creditordays-criteria/",
    views.ajax_creditordays_criteria,
    name="ajax_creditordays_criteria",),

    path(
    "client/<int:client_id>/ajax/stockdays-criteria/",
    views.ajax_stockdays_criteria,
    name="ajax_stockdays_criteria",),







]


