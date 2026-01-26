from __future__ import annotations
from django.db import connection
from typing import List, Dict, Any, Optional


from vfd_pro.common.db import (
    fetch_one_dict,
    fetch_all_dicts,
    fetch_scalar,
    callproc_one_dict,
    callproc_all_dicts,
)

import logging

sp_logger = logging.getLogger("sp_logger")


from typing import Any, Dict, List, Optional


def _get_caam_report(
    company_id: int, client_id: Optional[int] = None
) -> List[Dict[str, Any]]:

    try:
        params = [company_id, None if client_id is None else int(client_id)]
        rows = callproc_all_dicts("sp_get_caam_report", params)
        return rows or []

    except Exception as exc:
        sp_logger.error(
            "ERROR in _get_caam_report(company_id=%s, client_id=%s): %s",
            company_id,
            client_id,
            exc,
            exc_info=True,
        )
        raise


def _get_caam_report_details(company_id: int, client_id: int) -> Optional[dict]:

    sql = """
        SELECT *
        FROM tbl_process_caam_report
        WHERE company_id = %s
          AND client_id = %s
        ORDER BY reporting_date DESC
        LIMIT 1
    """
    return fetch_one_dict(sql, [company_id, client_id])


def _get_caam_report_config(client_id: int) -> Optional[dict]:
    sql = """
        SELECT *
        FROM vw_caam_report_config
        WHERE client_id = %s
        LIMIT 1
    """
    return fetch_one_dict(sql, [client_id])


def _get_caam_report_config_by_company(company_id: int) -> Optional[dict]:
    sql = """
        SELECT *
        FROM vw_caam_report_config
        WHERE company_id IN (%s, 0)
        ORDER BY 
            CASE 
                WHEN company_id = %s THEN 0
                ELSE 1
            END
        LIMIT 1
    """
    return fetch_one_dict(sql, [company_id, company_id])


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
