from django.urls import path
from vfd_pro.reports.caam.views import client_summary

from vfd_pro.reports.caam.api import (
    ajax_revenue_criteria,
    ajax_gm_criteria,
    ajax_oh_val_criteria,
    ajax_oh_pct_criteria,
    ajax_ebitda_criteria,
    ajax_newcust_criteria,
    ajax_retention_criteria,
    ajax_cash_criteria,
    ajax_debtordays_criteria,
    ajax_creditordays_criteria,
    ajax_stockdays_criteria,
)

app_name = "caam"

urlpatterns = [
    # path("reports/portfolio/", portfolio_view, name="portfolio"),
    # path("download-vfd/", download_vfd_report, name="download_vfd"),
    path("clients/<int:client_id>/summary/", client_summary, name="client_summary"),
    path(
        "clients/<int:client_id>/ajax/revenue/",
        ajax_revenue_criteria,
        name="ajax_revenue_criteria",
    ),
    path("clients/<int:client_id>/ajax/gm/", ajax_gm_criteria, name="ajax_gm_criteria"),
    path(
        "clients/<int:client_id>/ajax/oh-val/",
        ajax_oh_val_criteria,
        name="ajax_oh_val_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/oh-pct/",
        ajax_oh_pct_criteria,
        name="ajax_oh_pct_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/ebitda/",
        ajax_ebitda_criteria,
        name="ajax_ebitda_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/newcust/",
        ajax_newcust_criteria,
        name="ajax_newcust_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/retention/",
        ajax_retention_criteria,
        name="ajax_retention_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/cash/",
        ajax_cash_criteria,
        name="ajax_cash_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/debtordays/",
        ajax_debtordays_criteria,
        name="ajax_debtordays_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/creditordays/",
        ajax_creditordays_criteria,
        name="ajax_creditordays_criteria",
    ),
    path(
        "clients/<int:client_id>/ajax/stockdays/",
        ajax_stockdays_criteria,
        name="ajax_stockdays_criteria",
    ),
]
