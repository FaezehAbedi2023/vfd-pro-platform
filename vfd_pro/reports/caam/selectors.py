from __future__ import annotations
from django.db import connection
from vfd_pro.common.db import (
    fetch_one_dict,
    fetch_all_dicts,
    fetch_scalar,
    callproc_one_dict,
)

import logging

sp_logger = logging.getLogger("sp_logger")


def _get_client_kpi(client_id: int):
    return fetch_one_dict(
        "SELECT * FROM vw_vfd_client_kpis WHERE client_id = %s",
        [client_id],
    )


def _get_client_suitability(client_id: int):

    return fetch_one_dict(
        """
             SELECT
                client_id,

                is_24_month_history,
                CNT_months_with_sales_24,

                has_more_than_2_sales_nominals,
                CNT_sales_nominals_24,

                has_more_than_2_cos_nominals,
                CNT_cos_nominals_24,

                has_more_than_10_overhead_nominals,
                CNT_overhead_nominals_24,

                has_more_than_20_customers,
                CNT_customers_24,

                has_more_than_20_suppliers,
                CNT_suppliers_24,

                debtor_days_calculated,
                CNT_debtor_months,

                creditor_days_calculated,
                CNT_creditor_months,

                stock_days_calculated,
                CNT_stock_months,

                cash_balance_visible,
                CNT_cash_months,

                consistent_cost_base,
                CNT_inconsistent_months_12
                
            FROM vw_vfd_client_suitability
            WHERE client_id = %s
            """,
        [client_id],
    )


def _get_client_readiness(client_id: int):
    return fetch_one_dict(
        """
            SELECT
                client_id,
                client_name,

                is_ebitda_positive,
                val_ebitda_TY,
                val_ebitda_LY,
                is_ebitda_more_than_ly,
                val_ebitda_vs_ly,

                has_dividend_last_12m,
                val_dividend_TY,
                val_dividend_LY,
                is_dividend_at_least_equal_ly,
                val_dividend_vs_ly,

                is_cash_balance_positive,
                val_cash_TY,
                val_cash_LY,
                is_cash_more_than_ly,
                val_cash_vs_ly,

                are_sales_improving,
                val_revenue_TY,
                val_revenue_LY,
                val_revenue_vs_ly
            FROM vw_vfd_client_readiness
            WHERE client_id = %s
            """,
        [client_id],
    )


def _get_client_utilities(client_id: int):
    return fetch_one_dict(
        """
            SELECT has_utilities
            FROM vw_vfd_client_utilities
            WHERE client_id = %s
            """,
        [client_id],
    )


def _get_client_rd(client_id: int) -> str:
    return fetch_one_dict(
        "SELECT rd_flag FROM vw_vfd_client_rd WHERE client_id = %s",
        [client_id],
    )


def _get_sales_trend(client_id: int):
    return fetch_all_dicts(
        """
            SELECT offset, sales_month, sales_rolling_12_months
            FROM vfd_client_sales_trend
            WHERE client_id = %s
            ORDER BY offset
            """,
        [client_id],
    )


def _call_revenue_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_revenue_profitability",
        [client_id, period, sign_mode, min_months, threshold, flag_on],
    )


def _call_gm_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_gross_margin_profitability",
        [client_id, period, sign_mode, min_months, threshold, flag_on],
    )


def _call_overhead_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_overhead_profitability",
        [client_id, period, sign_mode, min_months, threshold, flag_on],
    )


def _call_overhead_pct_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_overhead_pct_profitability",
        [client_id, period, sign_mode, min_months, threshold, flag_on],
    )


def _call_ebitda_profitability_sp(client_id, sign_mode, min_months, threshold, flag_on):
    return callproc_one_dict(
        "sp_vfd_client_ebitda_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )


def _call_newcust_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_new_customers_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )


def _call_retention_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_retention_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )


def _call_cash_position_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_cash_position_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )


def _call_debtor_days_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_debtor_days_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )


def _call_creditor_days_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_creditor_days_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )


def _call_stock_days_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):
    return callproc_one_dict(
        "sp_vfd_client_stock_days_profitability",
        [client_id, sign_mode, min_months, threshold, flag_on],
    )
