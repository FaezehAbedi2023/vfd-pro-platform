from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict, Tuple, Optional
from vfd_pro.common.utils import fmt_percent, _fmt_num, _var_class
from django.http import Http404
from vfd_pro.reports.caam.selectors import _get_caam_report_config_by_company


def _is_yes(v) -> bool:
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("yes", "y", "true", "1")


def get_suitability(caam_row: dict) -> dict:
    top = [
        {
            "key": "24m_history",
            "label": "24M History",
            "is_yes": _is_yes(caam_row.get("suit_is_24_month_history")),
        },
        {
            "key": "gt2_sales",
            "label": ">2 Sales",
            "is_yes": _is_yes(caam_row.get("suit_has_more_than_2_sales_nominals")),
        },
        {
            "key": "gt2_cos",
            "label": ">2 COS",
            "is_yes": _is_yes(caam_row.get("suit_has_more_than_2_cos_nominals")),
        },
        {
            "key": "gt10_oh",
            "label": ">10 Overheads",
            "is_yes": _is_yes(caam_row.get("suit_has_more_than_10_overhead_nominals")),
        },
        {
            "key": "gt20_cust",
            "label": ">20 Customers",
            "is_yes": _is_yes(caam_row.get("suit_has_more_than_20_customers")),
        },
        {
            "key": "gt20_supp",
            "label": ">20 Suppliersxxxxxxxxxxxxxx",
            "is_yes": _is_yes(caam_row.get("suit_has_more_than_20_suppliers")),
        },
    ]

    bottom = [
        {
            "key": "debtors",
            "label": "Debtors Calc",
            "is_yes": _is_yes(caam_row.get("suit_debtor_days_calculated")),
        },
        {
            "key": "creditors",
            "label": "Creditors Calc",
            "is_yes": _is_yes(caam_row.get("suit_creditor_days_calculated")),
        },
        {
            "key": "stock",
            "label": "Stock Calc",
            "is_yes": _is_yes(caam_row.get("suit_stock_days_calculated")),
        },
        {
            "key": "cash",
            "label": "Cash Visiblexxxxxxxxxxxxxxx",
            "is_yes": _is_yes(caam_row.get("suit_flg_cash_balance_visible")),
        },
        {
            "key": "consistent_cost",
            "label": "Consistent Cost",
            "is_yes": _is_yes(caam_row.get("suit_consistent_cost_base")),
        },
    ]

    return {
        "top": top,
        "bottom": bottom,
    }


def get_suitability_settings(caam_row: dict, cfg: dict) -> dict:

    target = cfg.get("suitability_target_percent")

    def _enabled_flags(val):
        v = str(val or "").strip()
        is_yes = _is_yes(v)
        return v, is_yes, (not is_yes)

    rows = []

    # ---------- 24M History ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_24_months_history_enable", "Yes")
    )
    rows.append(
        {
            "key": "24m_history",
            "label": "24 Months History",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_months_with_sales_24"),
            "status": _is_yes(caam_row.get("suit_is_24_month_history")),
        }
    )

    # ---------- >2 Sales ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_more_than_2_sales_nominals_enable", "Yes")
    )
    rows.append(
        {
            "key": "gt2_sales",
            "label": "More Than 2 Sales Nominals",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_sales_nominals_24"),
            "status": _is_yes(caam_row.get("suit_has_more_than_2_sales_nominals")),
        }
    )

    # ---------- >2 COS ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_more_than_2_cos_nominals_enable", "Yes")
    )
    rows.append(
        {
            "key": "gt2_cos",
            "label": "More Than 2 COS Nominals",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_cos_nominals_24"),
            "status": _is_yes(caam_row.get("suit_has_more_than_2_cos_nominals")),
        }
    )

    # ---------- >10 Overheads ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_more_than_10_overhead_nominals_enable", "Yes")
    )
    rows.append(
        {
            "key": "gt10_oh",
            "label": "More Than 10 Overhead Nominals",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_overhead_nominals_24"),
            "status": _is_yes(caam_row.get("suit_has_more_than_10_overhead_nominals")),
        }
    )

    # ---------- >20 Customers ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_more_than_20_customers_enable", "Yes")
    )
    rows.append(
        {
            "key": "gt20_cust",
            "label": "More Than 20 Customers",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_customers_24"),
            "status": _is_yes(caam_row.get("suit_has_more_than_20_customers")),
        }
    )

    # ---------- >20 Suppliers ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_more_than_20_suppliers_enable", "Yes")
    )
    rows.append(
        {
            "key": "gt20_supp",
            "label": "More Than 20 Suppliers",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_suppliers_24"),
            "status": _is_yes(caam_row.get("suit_has_more_than_20_suppliers")),
        }
    )

    # ---------- Debtor Days ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_debtor_days_calculated_enable", "Yes")
    )
    rows.append(
        {
            "key": "debtors",
            "label": "Debtor Days Calculated",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_debtor_months"),
            "status": _is_yes(caam_row.get("suit_debtor_days_calculated")),
        }
    )
    # ---------- Creditor Days ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_creditor_days_calculated_enable", "Yes")
    )
    rows.append(
        {
            "key": "creditors",
            "label": "Creditor Days Calculated",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_creditor_months"),
            "status": _is_yes(caam_row.get("suit_creditor_days_calculated")),
        }
    )
    # ---------- Stock Days ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_stock_days_calculated_enable", "Yes")
    )
    rows.append(
        {
            "key": "stock",
            "label": "Stock Days Calculated",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_stock_months"),
            "status": _is_yes(caam_row.get("suit_stock_days_calculated")),
        }
    )
    # ---------- Cash Balance ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_cash_balance_visible_enable", "Yes")
    )
    rows.append(
        {
            "key": "cash",
            "label": "Cash Balance Visible",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_cash_months"),
            "status": _is_yes(caam_row.get("suit_flg_cash_balance_visible")),
        }
    )
    # ---------- Consistent Cost Base ----------
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_flags(
        cfg.get("suitability_consistent_cost_base_enable", "Yes")
    )
    rows.append(
        {
            "key": "gt_ccb",
            "label": "Consistent Cost Base",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "value": caam_row.get("suit_CNT_inconsistent_months_12"),
            "status": _is_yes(caam_row.get("suit_consistent_cost_base")),
        }
    )

    return {
        "target_percent": target,
        "rows": rows,
    }


def get_readiness(caam_row: dict) -> dict:

    top = [
        {
            "key": "ebitda_pos",
            "label": "EBITDA +",
            "status": _is_yes(caam_row.get("read_is_ebitda_positive")),
        },
        {
            "key": "ebitda_gt_ly",
            "label": "EBITDA > LY",
            "status": _is_yes(caam_row.get("read_is_ebitda_more_than_ly")),
        },
        {
            "key": "div_12m",
            "label": "Dividend (12m)",
            "status": _is_yes(caam_row.get("read_has_dividend_last_12m")),
        },
        {
            "key": "div_ge_ly",
            "label": "Dividend ≥ LY",
            "status": _is_yes(caam_row.get("read_is_dividend_at_least_equal_ly")),
        },
    ]

    bottom = [
        {
            "key": "cash_pos",
            "label": "Cash +",
            "status": _is_yes(caam_row.get("read_is_cash_balance_positive")),
        },
        {
            "key": "cash_gt_ly",
            "label": "Cash > LY",
            "status": _is_yes(caam_row.get("read_is_cash_more_than_ly")),
        },
        {
            "key": "sales_improving",
            "label": "Sales Improving",
            "status": _is_yes(caam_row.get("read_are_sales_improving")),
        },
    ]

    return {"top": top, "bottom": bottom}


def get_readiness_settings(caam_row: dict, cfg: dict) -> dict:
    target = cfg.get("readiness_target_percent")

    def _enabled_vm(cfg_key: str, default="Yes"):
        enabled_val = cfg.get(cfg_key, default)
        is_yes = _is_yes(enabled_val)
        return enabled_val, is_yes, (not is_yes)

    rows = []

    # 1) EBITDA positive?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_ebitda_positive_enable"
    )
    rows.append(
        {
            "key": "ebitda_positive",
            "label": "Is The Client's EBITDA Positive?",
            "enabled_name": "readiness_ebitda_positive_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_ebitda_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_ebitda_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_ebitda_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_is_ebitda_positive")),
        }
    )

    # 2) EBITDA more than LY?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_ebitda_more_than_last_year_enable"
    )
    rows.append(
        {
            "key": "ebitda_more_than_ly",
            "label": "Is The EBITDA More Than Last Year?",
            "enabled_name": "readiness_ebitda_more_than_last_year_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_ebitda_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_ebitda_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_ebitda_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_is_ebitda_more_than_ly")),
        }
    )

    # 3) Dividend last 12m?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_paid_dividend_last_12m_enable"
    )
    rows.append(
        {
            "key": "dividend_last_12m",
            "label": "Have They Paid A Dividend In The Last 12 Months?",
            "enabled_name": "readiness_paid_dividend_last_12m_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_dividend_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_dividend_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_dividend_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_has_dividend_last_12m")),
        }
    )

    # 4) Dividend at least equal LY?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_dividend_at_least_last_year_enable"
    )
    rows.append(
        {
            "key": "dividend_at_least_ly",
            "label": "Is The Dividend At Least Equal To Last Year?",
            "enabled_name": "readiness_dividend_at_least_last_year_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_dividend_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_dividend_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_dividend_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_is_dividend_at_least_equal_ly")),
        }
    )

    # 5) Cash balance positive?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_cash_positive_enable"
    )
    rows.append(
        {
            "key": "cash_positive",
            "label": "Is The Cash Balance Positive?",
            "enabled_name": "readiness_cash_positive_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_cash_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_cash_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_cash_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_is_cash_balance_positive")),
        }
    )

    # 6) Cash more than LY?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_cash_more_than_last_year_enable"
    )
    rows.append(
        {
            "key": "cash_more_than_ly",
            "label": "Is The Cash Balance More Than Last Year?",
            "enabled_name": "readiness_cash_more_than_last_year_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_cash_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_cash_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_cash_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_is_cash_more_than_ly")),
        }
    )

    # 7) Sales improving?
    enabled_val, enabled_is_yes, enabled_is_no = _enabled_vm(
        "readiness_sales_improving_enable"
    )
    rows.append(
        {
            "key": "sales_improving",
            "label": "Are Sales Improving?",
            "enabled_name": "readiness_sales_improving_enable",
            "enabled": enabled_val,
            "enabled_is_yes": enabled_is_yes,
            "enabled_is_no": enabled_is_no,
            "ty": _fmt_num(caam_row.get("read_val_revenue_TY"), 1),
            "ly": _fmt_num(caam_row.get("read_val_revenue_LY"), 1),
            "vs": _fmt_num(caam_row.get("read_val_revenue_vs_ly"), 1),
            "status": _is_yes(caam_row.get("read_are_sales_improving")),
        }
    )

    return {"target_percent": target, "rows": rows}


def get_performance_kpi(caam_row: dict) -> dict:

    def _sign_class(v):

        if v is None:
            return ""
        try:
            if v < 0:
                return "text-danger"
            if v > 0:
                return "text-success"
        except TypeError:
            return ""
        return ""

    rows = [
        {
            "key": "revenue",
            "label": "Revenue",
            "ty": caam_row.get("KPI_revenue_TY"),
            "ly": caam_row.get("KPI_revenue_LY"),
            "var": caam_row.get("KPI_rev_var"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_rev_var")),
        },
        {
            "key": "gm_pct",
            "label": "Gross Margin %",
            "ty": caam_row.get("KPI_gross_margin_pct_TY"),
            "ly": caam_row.get("KPI_gross_margin_pct_LY"),
            "var": caam_row.get("KPI_gross_margin_vs_LY_pct"),
            "var_suffix": "%",
            "var_class": _sign_class(caam_row.get("KPI_gross_margin_vs_LY_pct")),
        },
        {
            "key": "overheads",
            "label": "Overheads",
            "ty": caam_row.get("KPI_overheads_TY"),
            "ly": caam_row.get("KPI_overheads_LY"),
            "var": caam_row.get("KPI_ovh_var"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_ovh_var")),
        },
        {
            "key": "ebitda",
            "label": "EBITDA",
            "ty": caam_row.get("KPI_ebitda_TY"),
            "ly": caam_row.get("KPI_ebitda_LY"),
            "var": caam_row.get("KPI_ebitda_vs_LY_value"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_ebitda_vs_LY_value")),
        },
        {
            "key": "ebitda_pct",
            "label": "EBITDA %",
            "ty": caam_row.get("KPI_ebitda_pct_TY"),
            "ly": caam_row.get("KPI_ebitda_pct_LY"),
            "var": caam_row.get("KPI_ebitda_pct_vs_LY"),
            "var_suffix": "%",
            "var_class": _sign_class(caam_row.get("KPI_ebitda_pct_vs_LY")),
        },
    ]

    return {"rows": rows}


def get_working_capital_kpi(caam_row: dict) -> dict:

    def _sign_class(v):
        if v is None:
            return ""
        try:
            if v < 0:
                return "text-danger"
            if v > 0:
                return "text-success"
        except TypeError:
            return ""
        return ""

    rows = [
        {
            "key": "cash_position",
            "label": "Cash Position",
            "ty": caam_row.get("KPI_cash_position_TY"),
            "ly": caam_row.get("KPI_cash_position_LY"),
            "var": caam_row.get("KPI_cash_position_vs_LY"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_cash_position_vs_LY")),
        },
        {
            "key": "debtor_days",
            "label": "Debtor Days",
            "ty": caam_row.get("KPI_debtor_days_TY"),
            "ly": caam_row.get("KPI_debtor_days_LY"),
            "var": caam_row.get("KPI_debtor_days_vs_LY"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_debtor_days_vs_LY")),
        },
        {
            "key": "creditor_days",
            "label": "Creditor Days",
            "ty": caam_row.get("KPI_creditor_days_TY"),
            "ly": caam_row.get("KPI_creditor_days_LY"),
            "var": caam_row.get("KPI_creditor_days_vs_LY"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_creditor_days_vs_LY")),
        },
        {
            "key": "stock_days",
            "label": "Stock Days",
            "ty": caam_row.get("KPI_stock_days_TY"),
            "ly": caam_row.get("KPI_stock_days_LY"),
            "var": caam_row.get("KPI_stock_days_vs_LY"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_stock_days_vs_LY")),
        },
        {
            "key": "dividend",
            "label": "Dividend",
            "ty": caam_row.get("KPI_dividend_TY"),
            "ly": caam_row.get("KPI_dividend_LY"),
            "var": caam_row.get("KPI_div_var"),
            "var_suffix": "",
            "var_class": _sign_class(caam_row.get("KPI_div_var")),
        },
    ]

    return {"rows": rows}


def get_iht_settings(caam_row: dict, cfg: dict) -> dict:

    enabled_val = cfg.get("iht_enable", "No")
    enabled_is_yes = _is_yes(enabled_val)

    threshold_val = cfg.get("iht_valuation_threshold")
    multiple_val = cfg.get("multiple")
    ebitda_ty_val = caam_row.get("opp_EBITDA_TY_12m")
    est_val = caam_row.get("iht_est_valuation")
    risk_flag_val = caam_row.get("iht_risk_flag")
    risk_flag_bool = _is_yes(risk_flag_val)

    return {
        "enabled_name": "iht_enable",
        "enabled": enabled_val,
        "enabled_is_yes": enabled_is_yes,
        "enabled_is_no": (not enabled_is_yes),
        "ebitda_ty": _fmt_num(ebitda_ty_val),
        "multiple_name": "multiple",
        "multiple": multiple_val,
        "threshold_name": "iht_valuation_threshold",
        "threshold": threshold_val,
        "estimated_business_value": _fmt_num(est_val),
        "risk_flag": risk_flag_bool,
    }


def get_performance_settings(cfg: dict, caam_row: dict, p_period_str: str) -> dict:

    def _yesno_vm(cfg: dict, cfg_key: str) -> dict:

        val = cfg.get(cfg_key)
        is_yes = _is_yes(val)
        return {
            "value": val,
            "is_yes": is_yes,
            "is_no": not is_yes,
        }

    def _sign_vm(cfg: dict, cfg_key: str) -> dict:
        val = str(cfg.get(cfg_key) or "").strip()
        return {
            "value": val,
            "is_pm": val == "+/-",
            "is_plus": val == "+",
            "is_minus": val == "-",
        }

    def _threshold_vm(cfg: dict, cfg_key: str) -> dict:
        return {"value": cfg.get(cfg_key)}

    def _period_vm(cfg: dict, p_period_str: str) -> dict:
        val = str(p_period_str or cfg.get("p_period") or "").strip()
        return {
            "id": "p_period",
            "name": "p_period",
            "value": val,
            "is_12": val == "12",
            "is_6": val == "6",
            "is_3": val == "3",
        }

    revenue_last12 = caam_row.get("opp_Revenue_vs_LY_12m_pct")
    revenue_last6 = caam_row.get("opp_Revenue_vs_LY_6m_pct")
    revenue_last3 = caam_row.get("opp_Revenue_vs_LY_3m_pct")
    revenue_impact_profit = caam_row.get("opp_Revenue_Impact_Profit")
    revenue_val_impact = caam_row.get("opp_Revenue_val_impact")

    gm_last12 = caam_row.get("opp_gm_pct_vs_ly_12m")
    gm_last6 = caam_row.get("opp_gm_pct_vs_ly_6m")
    gm_last3 = caam_row.get("opp_gm_pct_vs_ly_3m")
    gm_impact_profit = caam_row.get("opp_gm_profit_impact")
    gm_val_impact = caam_row.get("opp_gm_val_impact")

    oh_last12 = caam_row.get("opp_Overheads_vs_LY_12m_pct")
    oh_last6 = caam_row.get("opp_Overheads_vs_LY_6m_pct")
    oh_last3 = caam_row.get("opp_Overheads_vs_LY_3m_pct")
    oh_impact_profit = caam_row.get("opp_Overheads_profit_impact")
    oh_val_impact = caam_row.get("opp_Overheads_val_impact")

    ohpct_last12 = caam_row.get("opp_Overhead_pct_vs_LY_12m")
    ohpct_last6 = caam_row.get("opp_Overhead_pct_vs_LY_6m")
    ohpct_last3 = caam_row.get("opp_Overhead_pct_vs_LY_3m")
    ohpct_impact_profit = caam_row.get("opp_Overhead_pct_profit_impact")
    ohpct_val_impact = caam_row.get("opp_Overhead_pct_val_impact")

    ebitda_ty = caam_row.get("opp_EBITDA_TY_12m")
    ebitda_ly = caam_row.get("opp_EBITDA_LY_12m")
    ebitda_var_pct = caam_row.get("opp_EBITDA_vs_LY_12m_pct")
    ebitda_var_value = caam_row.get("opp_EBITDA_vs_LY_12m")
    ebitda_impact_profit = caam_row.get("opp_EBITDA_profit_impact")

    nc_ty = caam_row.get("opp_NewCust_TY")
    nc_ly = caam_row.get("opp_NewCust_LY")
    nc_var_pct = caam_row.get("opp_NewCust_Var_pct")

    cr_ty = caam_row.get("opp_Retention_TY")
    cr_ly = caam_row.get("opp_Retention_LY")
    cr_var_pct = caam_row.get("opp_Retention_Var_pct")

    group1 = [
        {
            "key": "revenue",
            "label": "Revenue",
            "enable": {
                "id": "p_revenue_enable",
                "name": "p_revenue_enable",
                **_yesno_vm(cfg, "p_revenue_enable"),
            },
            "sign": {
                "id": "p_revenue_sign_mode",
                "name": "p_revenue_sign_mode",
                **_sign_vm(cfg, "p_revenue_sign_mode"),
            },
            "threshold": {
                "id": "p_revenue_threshold_percent",
                "name": "p_revenue_threshold_percent",
                **_threshold_vm(cfg, "p_revenue_threshold_percent"),
            },
            "actual": {
                "last12": {
                    "id": "opp_revenue_last12",
                    "raw": revenue_last12,
                    "value": fmt_percent(revenue_last12, 1),
                    "class": _var_class(revenue_last12),
                },
                "last6": {
                    "id": "opp_revenue_last6",
                    "raw": revenue_last6,
                    "value": fmt_percent(revenue_last6, 1),
                    "class": _var_class(revenue_last6),
                },
                "last3": {
                    "id": "opp_revenue_last3",
                    "raw": revenue_last3,
                    "value": fmt_percent(revenue_last3, 1),
                    "class": _var_class(revenue_last3),
                },
            },
            "flag": {
                "id": "opp_rev_flag_icon",
                "status": _is_yes(caam_row.get("opp_rev_flag")),
            },
            "profit_impact": {
                "id": "opp_Revenue_Impact_Profit",
                "raw": revenue_impact_profit,
                "value": _fmt_num(revenue_impact_profit, 1),
                "class": _var_class(revenue_impact_profit),
            },
            "val_impact": {
                "id": "opp_Revenue_val_impact",
                "raw": revenue_val_impact,
                "value": _fmt_num(revenue_val_impact, 1),
                "class": _var_class(revenue_val_impact),
            },
        },
        {
            "key": "gm",
            "label": "Gross Margin %",
            "enable": {
                "id": "p_gm_enable",
                "name": "p_gm_enable",
                **_yesno_vm(cfg, "p_gm_enable"),
            },
            "sign": {
                "id": "p_gm_sign_mode",
                "name": "p_gm_sign_mode",
                **_sign_vm(cfg, "p_gm_sign_mode"),
            },
            "threshold": {
                "id": "p_gm_threshold_percent",
                "name": "p_gm_threshold_percent",
                **_threshold_vm(cfg, "p_gm_threshold_percent"),
            },
            "actual": {
                "last12": {
                    "id": "opp_gm_last12",
                    "raw": gm_last12,
                    "value": fmt_percent(gm_last12, 1),
                    "class": _var_class(gm_last12),
                },
                "last6": {
                    "id": "opp_gm_last6",
                    "raw": gm_last6,
                    "value": fmt_percent(gm_last6, 1),
                    "class": _var_class(gm_last6),
                },
                "last3": {
                    "id": "opp_gm_last3",
                    "raw": gm_last3,
                    "value": fmt_percent(gm_last3, 1),
                    "class": _var_class(gm_last3),
                },
            },
            "flag": {
                "id": "opp_gm_flag_icon",
                "status": _is_yes(caam_row.get("opp_gm_flag")),
            },
            "profit_impact": {
                "id": "opp_gm_profit_impact",
                "raw": gm_impact_profit,
                "value": _fmt_num(gm_impact_profit, 1),
                "class": _var_class(gm_impact_profit),
            },
            "val_impact": {
                "id": "opp_gm_val_impact",
                "raw": gm_val_impact,
                "value": _fmt_num(gm_val_impact, 1),
                "class": _var_class(gm_val_impact),
            },
        },
        {
            "key": "oh",
            "label": "Overhead £",
            "enable": {
                "id": "p_oh_enable",
                "name": "p_oh_enable",
                **_yesno_vm(cfg, "p_oh_enable"),
            },
            "sign": {
                "id": "p_oh_sign_mode",
                "name": "p_oh_sign_mode",
                **_sign_vm(cfg, "p_oh_sign_mode"),
            },
            "threshold": {
                "id": "p_oh_threshold_percent",
                "name": "p_oh_threshold_percent",
                **_threshold_vm(cfg, "p_oh_threshold_percent"),
            },
            "actual": {
                "last12": {
                    "id": "opp_oh_last12",
                    "raw": oh_last12,
                    "value": fmt_percent(oh_last12, 1),
                    "class": _var_class(oh_last12),
                },
                "last6": {
                    "id": "opp_oh_last6",
                    "raw": oh_last6,
                    "value": fmt_percent(oh_last6, 1),
                    "class": _var_class(oh_last6),
                },
                "last3": {
                    "id": "opp_oh_last3",
                    "raw": oh_last3,
                    "value": fmt_percent(oh_last3, 1),
                    "class": _var_class(oh_last3),
                },
            },
            "flag": {
                "id": "opp_oh_flag_icon",
                "status": _is_yes(caam_row.get("opp_oh_flag")),
            },
            "profit_impact": {
                "id": "opp_Overheads_profit_impact",
                "raw": oh_impact_profit,
                "value": _fmt_num(oh_impact_profit, 1),
                "class": _var_class(oh_impact_profit),
            },
            "val_impact": {
                "id": "opp_Overheads_val_impact",
                "raw": oh_val_impact,
                "value": _fmt_num(oh_val_impact, 1),
                "class": _var_class(oh_val_impact),
            },
        },
        {
            "key": "oh_pct",
            "label": "Overhead %",
            "enable": {
                "id": "p_oh_pct_enable",
                "name": "p_oh_pct_enable",
                **_yesno_vm(cfg, "p_oh_pct_enable"),
            },
            "sign": {
                "id": "p_oh_pct_sign_mode",
                "name": "p_oh_pct_sign_mode",
                **_sign_vm(cfg, "p_oh_pct_sign_mode"),
            },
            "threshold": {
                "id": "p_oh_pct_threshold_percent",
                "name": "p_oh_pct_threshold_percent",
                **_threshold_vm(cfg, "p_oh_pct_threshold_percent"),
            },
            "actual": {
                "last12": {
                    "id": "opp_ohp_last12",
                    "raw": ohpct_last12,
                    "value": fmt_percent(ohpct_last12, 1),
                    "class": _var_class(ohpct_last12),
                },
                "last6": {
                    "id": "opp_ohp_last6",
                    "raw": ohpct_last6,
                    "value": fmt_percent(ohpct_last6, 1),
                    "class": _var_class(ohpct_last6),
                },
                "last3": {
                    "id": "opp_ohp_last3",
                    "raw": ohpct_last3,
                    "value": fmt_percent(ohpct_last3, 1),
                    "class": _var_class(ohpct_last3),
                },
            },
            "flag": {
                "id": "opp_ohp_flag_icon",
                "status": _is_yes(caam_row.get("opp_ohp_flag")),
            },
            "profit_impact": {
                "id": "opp_Overhead_pct_profit_impact",
                "raw": ohpct_impact_profit,
                "value": _fmt_num(ohpct_impact_profit, 1),
                "class": _var_class(ohpct_impact_profit),
            },
            "val_impact": {
                "id": "opp_Overhead_pct_val_impact",
                "raw": ohpct_val_impact,
                "value": _fmt_num(ohpct_val_impact, 1),
                "class": _var_class(ohpct_val_impact),
            },
        },
    ]

    group2 = [
        {
            "key": "ebitda",
            "label": "EBITDA £",
            "enable": {
                "id": "p_ebitda_enable",
                "name": "p_ebitda_enable",
                **_yesno_vm(cfg, "p_ebitda_enable"),
            },
            "sign": {
                "id": "p_ebitda_sign_mode",
                "name": "p_ebitda_sign_mode",
                **_sign_vm(cfg, "p_ebitda_sign_mode"),
            },
            "threshold": {
                "id": "p_ebitda_threshold_percent",
                "name": "p_ebitda_threshold_percent",
                **_threshold_vm(cfg, "p_ebitda_threshold_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_ebitda_ty_12m",
                    "raw": ebitda_ty,
                    "value": _fmt_num(ebitda_ty, 1),
                    "class": _var_class(ebitda_ty),
                },
                "ly": {
                    "id": "opp_ebitda_ly_12m",
                    "raw": ebitda_ly,
                    "value": _fmt_num(ebitda_ly, 1),
                    "class": _var_class(ebitda_ly),
                },
                "varp": {
                    "id": "opp_ebitda_var_pct",
                    "raw": ebitda_var_pct,
                    "value": fmt_percent(ebitda_var_pct, 1),
                    "class": _var_class(ebitda_var_pct),
                },
                "varv": {
                    "id": "opp_ebitda_var_val",
                    "raw": ebitda_var_value,
                    "value": _fmt_num(ebitda_var_value, 1),
                    "class": _var_class(ebitda_var_value),
                },
            },
            "flag": {
                "id": "opp_eb_flag_icon",
                "status": _is_yes(caam_row.get("opp_eb_flag")),
            },
            "impact": {
                "id": "opp_ebitda_impact",
                "raw": ebitda_impact_profit,
                "value": _fmt_num(ebitda_impact_profit, 1),
                "class": _var_class(ebitda_impact_profit),
            },
        }
    ]

    group3 = [
        {
            "key": "ncust",
            "label": "New Customers",
            "enable": {
                "id": "p_ncust_enable",
                "name": "p_ncust_enable",
                **_yesno_vm(cfg, "p_ncust_enable"),
            },
            "sign": {
                "id": "p_ncust_sign_mode",
                "name": "p_ncust_sign_mode",
                **_sign_vm(cfg, "p_ncust_sign_mode"),
            },
            "threshold": {
                "id": "p_ncust_threshold_percent",
                "name": "p_ncust_threshold_percent",
                **_threshold_vm(cfg, "p_ncust_threshold_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_ncust_ty",
                    "raw": nc_ty,
                    "value": _fmt_num(nc_ty, 1),
                    "class": _var_class(nc_ty),
                },
                "ly": {
                    "id": "opp_ncust_ly",
                    "raw": nc_ly,
                    "value": _fmt_num(nc_ly, 1),
                    "class": _var_class(nc_ly),
                },
                "varp": {
                    "id": "opp_ncust_var_pct",
                    "raw": nc_var_pct,
                    "value": _fmt_num(nc_var_pct, 1),
                    "class": _var_class(nc_var_pct),
                },
            },
            "flag": {
                "id": "opp_nc_flag_icon",
                "status": _is_yes(caam_row.get("opp_nc_flag")),
            },
        },
        {
            "key": "retention",
            "label": "Client Retention",
            "enable": {
                "id": "p_retention_enable",
                "name": "p_retention_enable",
                **_yesno_vm(cfg, "p_retention_enable"),
            },
            "sign": {
                "id": "p_retention_sign_mode",
                "name": "p_retention_sign_mode",
                **_sign_vm(cfg, "p_retention_sign_mode"),
            },
            "threshold": {
                "id": "p_retention_threshold_percent",
                "name": "p_retention_threshold_percent",
                **_threshold_vm(cfg, "p_retention_threshold_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_ret_ty",
                    "raw": cr_ty,
                    "value": _fmt_num(cr_ty, 1),
                    "class": _var_class(cr_ty),
                },
                "ly": {
                    "id": "opp_ret_ly",
                    "raw": cr_ly,
                    "value": _fmt_num(cr_ly, 1),
                    "class": _var_class(cr_ly),
                },
                "varp": {
                    "id": "opp_ret_var_pct",
                    "raw": cr_var_pct,
                    "value": fmt_percent(cr_var_pct, 1),
                    "class": _var_class(cr_var_pct),
                },
            },
            "flag": {
                "id": "opp_ret_flag_icon",
                "status": _is_yes(caam_row.get("opp_ret_flag")),
            },
        },
    ]

    return {
        "period": _period_vm(cfg, p_period_str),
        "multiple": {
            "id": "opp_multiple",
            "name": "opp_multiple",
            "value": cfg.get("multiple"),
        },
        "group1": group1,
        "group2": group2,
        "group3": group3,
    }


def get_working_capital_settings(cfg: dict, row: dict) -> dict:

    def _yesno_vm(cfg_key: str) -> dict:
        val = cfg.get(cfg_key)
        is_yes = _is_yes(val)
        return {"value": val, "is_yes": is_yes, "is_no": (not is_yes)}

    def _sign_vm(cfg_key: str) -> dict:
        val = str(cfg.get(cfg_key) or "").strip()
        return {
            "value": val,
            "is_pm": val == "+/-",
            "is_plus": val == "+",
            "is_minus": val == "-",
        }

    def _var_vm(cfg_key: str) -> dict:
        return {"value": cfg.get(cfg_key)}

    cp_ty = row.get("opp_Cash_TY")
    cp_ly = row.get("opp_Cash_LY")
    cp_var_pct = row.get("opp_Cash_vs_LY_pct")
    cp_var_value = row.get("opp_Cash_vs_LY_value")

    dd_ty = row.get("opp_DebtorDays_TY")
    dd_ly = row.get("opp_DebtorDays_LY")
    dd_var_pct = row.get("opp_DebtorDays_Var_pct")
    dd_var_value = row.get("opp_DebtorDays_Var_value")

    cd_ty = row.get("opp_CreditorDays_TY")
    cd_ly = row.get("opp_CreditorDays_LY")
    cd_var_pct = row.get("opp_CreditorDays_Var_pct")
    cd_var_value = row.get("opp_CreditorDays_Var_value")

    sd_ty = row.get("opp_StockDays_TY")
    sd_ly = row.get("opp_StockDays_LY")
    sd_var_pct = row.get("opp_StockDays_Var_pct")
    sd_var_value = row.get("opp_StockDays_Var_value")

    rows = [
        {
            "key": "cash_position",
            "label": "Cash Position",
            "enable": {
                "id": "p_cp_enable",
                "name": "p_cp_enable",
                **_yesno_vm("p_cp_enable"),
            },
            "sign": {
                "id": "p_cp_sign_mode",
                "name": "p_cp_sign_mode",
                **_sign_vm("p_cp_sign_mode"),
            },
            "var": {
                "id": "p_cp_var_percent",
                "name": "p_cp_var_percent",
                **_var_vm("p_cp_var_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_cp_ty",
                    "raw": cp_ty,
                    "value": _fmt_num(cp_ty, 1),
                    "class": _var_class(cp_ty),
                },
                "ly": {
                    "id": "opp_cp_ly",
                    "raw": cp_ly,
                    "value": _fmt_num(cp_ly, 1),
                    "class": _var_class(cp_ly),
                },
                "var_pct": {
                    "id": "opp_cp_var_pct",
                    "raw": cp_var_pct,
                    "value": fmt_percent(cp_var_pct, 1),
                    "class": _var_class(cp_var_pct),
                },
                "var_val": {
                    "id": "opp_cp_var_val",
                    "raw": cp_var_value,
                    "value": _fmt_num(cp_var_value, 1),
                    "class": _var_class(cp_var_value),
                },
            },
            "flag": {
                "id": "opp_cp_flag_icon",
                "status": _is_yes(row.get("opp_cp_flag")),
            },
        },
        {
            "key": "debtor_days",
            "label": "Debtor Days",
            "enable": {
                "id": "p_ddays_enable",
                "name": "p_ddays_enable",
                **_yesno_vm("p_ddays_enable"),
            },
            "sign": {
                "id": "p_ddays_sign_mode",
                "name": "p_ddays_sign_mode",
                **_sign_vm("p_ddays_sign_mode"),
            },
            "var": {
                "id": "p_ddays_var_percent",
                "name": "p_ddays_var_percent",
                **_var_vm("p_ddays_var_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_dd_ty",
                    "raw": dd_ty,
                    "value": _fmt_num(dd_ty, 1),
                    "class": _var_class(dd_ty),
                },
                "ly": {
                    "id": "opp_dd_ly",
                    "raw": dd_ly,
                    "value": _fmt_num(dd_ly, 1),
                    "class": _var_class(dd_ly),
                },
                "var_pct": {
                    "id": "opp_dd_var_pct",
                    "raw": dd_var_pct,
                    "value": fmt_percent(dd_var_pct, 1),
                    "class": _var_class(dd_var_pct),
                },
                "var_val": {
                    "id": "opp_dd_var_val",
                    "raw": dd_var_value,
                    "value": _fmt_num(dd_var_value, 1),
                    "class": _var_class(dd_var_value),
                },
            },
            "flag": {
                "id": "opp_dd_flag_icon",
                "status": _is_yes(row.get("opp_dd_flag")),
            },
        },
        {
            "key": "creditor_days",
            "label": "Creditor Days",
            "enable": {
                "id": "p_cdays_enable",
                "name": "p_cdays_enable",
                **_yesno_vm("p_cdays_enable"),
            },
            "sign": {
                "id": "p_cdays_sign_mode",
                "name": "p_cdays_sign_mode",
                **_sign_vm("p_cdays_sign_mode"),
            },
            "var": {
                "id": "p_cdays_var_percent",
                "name": "p_cdays_var_percent",
                **_var_vm("p_cdays_var_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_cd_ty",
                    "raw": cd_ty,
                    "value": _fmt_num(cd_ty, 1),
                    "class": _var_class(cd_ty),
                },
                "ly": {
                    "id": "opp_cd_ly",
                    "raw": cd_ly,
                    "value": _fmt_num(cd_ly, 1),
                    "class": _var_class(cd_ly),
                },
                "var_pct": {
                    "id": "opp_cd_var_pct",
                    "raw": cd_var_pct,
                    "value": fmt_percent(cd_var_pct, 1),
                    "class": _var_class(cd_var_pct),
                },
                "var_val": {
                    "id": "opp_cd_var_val",
                    "raw": cd_var_value,
                    "value": _fmt_num(cd_var_value, 1),
                    "class": _var_class(cd_var_value),
                },
            },
            "flag": {
                "id": "opp_cd_flag_icon",
                "status": _is_yes(row.get("opp_cd_flag")),
            },
        },
        {
            "key": "stock_days",
            "label": "Stock Days",
            "enable": {
                "id": "p_sdays_enable",
                "name": "p_sdays_enable",
                **_yesno_vm("p_sdays_enable"),
            },
            "sign": {
                "id": "p_sdays_sign_mode",
                "name": "p_sdays_sign_mode",
                **_sign_vm("p_sdays_sign_mode"),
            },
            "var": {
                "id": "p_sdays_var_percent",
                "name": "p_sdays_var_percent",
                **_var_vm("p_sdays_var_percent"),
            },
            "actual": {
                "ty": {
                    "id": "opp_sd_ty",
                    "raw": sd_ty,
                    "value": _fmt_num(sd_ty, 1),
                    "class": _var_class(sd_ty),
                },
                "ly": {
                    "id": "opp_sd_ly",
                    "raw": sd_ly,
                    "value": _fmt_num(sd_ly, 1),
                    "class": _var_class(sd_ly),
                },
                "var_pct": {
                    "id": "opp_sd_var_pct",
                    "raw": sd_var_pct,
                    "value": fmt_percent(sd_var_pct, 1),
                    "class": _var_class(sd_var_pct),
                },
                "var_val": {
                    "id": "opp_sd_var_val",
                    "raw": sd_var_value,
                    "value": _fmt_num(sd_var_value, 1),
                    "class": _var_class(sd_var_value),
                },
            },
            "flag": {
                "id": "opp_sd_flag_icon",
                "status": _is_yes(row.get("opp_sd_flag")),
            },
        },
    ]

    return {"rows": rows}


def build_company_settings_modal_context(company_id: int) -> dict:

    cfg = _get_caam_report_config_by_company(company_id) or {}
    empty_row = {}

    p_period_str = str(cfg.get("p_period") or "12")

    return {
        "company_id": company_id,
        "suitability_settings": get_suitability_settings(empty_row, cfg),
        "perf_settings": get_performance_settings(cfg, empty_row, p_period_str),
        "working_capital_settings": get_working_capital_settings(cfg, empty_row),
        "iht_settings": get_iht_settings(empty_row, cfg),
        "readiness_settings": get_readiness_settings(empty_row, cfg),
    }
