from __future__ import annotations
from decimal import Decimal
from typing import Any, Dict, Tuple, Optional

from django.http import Http404


# from vfd_pro.models import OpportunityCriteria faezeh

from vfd_pro.common.utils import (
    _fmt_num,
    fmt_percent,
    _var_class,
    _round10_or_none,
)

from .selectors import (
    _get_client_utilities,
    _get_client_rd,
    _get_client_kpi,
    _get_client_suitability,
    _get_client_readiness,
    _get_sales_trend,
)


# -----------------------------
# Opportunity Score
# -----------------------------
def calculate_opportunity_score(post_data) -> Tuple[Optional[int], Dict[str, Any]]:
    """
    همان منطق قبلی view:
    از POST می‌خواند و بر اساس enabled/flag ها امتیاز می‌دهد.
    خروجی:
      - opportunity_score (0..100 یا None)
      - kpi_state (برای ذخیره در DB)
    """
    kpis = [
        ("revenue", "rev_enabled", "rev_flag"),
        ("gm", "gm_enabled", "gm_flag"),
        ("oh_val", "oh_val_enabled", "oh_val_flag"),
        ("oh_pct", "oh_pct_enabled", "oh_pct_flag"),
        ("ebitda", "ebitda_enabled", "ebitda_flag"),
        ("newcust", "newcust_enabled", "newcust_flag"),
        ("retention", "retention_enabled", "retention_flag"),
        ("cash", "cash_enabled", "cash_flag"),
        ("debtordays", "debtordays_enabled", "debtordays_flag"),
        ("creditordays", "creditordays_enabled", "creditordays_flag"),
        ("stockdays", "stockdays_enabled", "stockdays_flag"),
    ]

    enabled_count = 0
    yes_count = 0

    kpi_state: Dict[str, Any] = {"criteria": {}}

    for key, enabled_field, flag_field in kpis:
        enabled = post_data.get(enabled_field, "Yes") == "Yes"
        flag_val = post_data.get(flag_field)

        kpi_state["criteria"][key] = {
            "enabled": enabled,
            "flag": flag_val,
        }

        if enabled:
            enabled_count += 1
            if str(flag_val).strip().lower() == "yes":
                yes_count += 1

    if enabled_count == 0:
        return None, kpi_state

    score = round(100 * yes_count / enabled_count)
    return score, kpi_state


# -----------------------------
# POST handler
# -----------------------------
SESSION_KEY_TMPL = "client_summary_state_{client_id}"


def handle_client_summary_post(post_data, client_id: int, session=None):

    # criteria, _ = OpportunityCriteria.objects.get_or_create(client_id=client_id)

    # opportunity_score, kpi_state = calculate_opportunity_score(request.POST)
    opportunity_score, kpi_state = calculate_opportunity_score(post_data)
    kpi_state = kpi_state or {}

    # ---- Suitability enable/disable config ----
    suit_cfg = {
        "is_24_month_history": post_data.get("is_24_month_history_enabled", "Yes")
        == "Yes",
        "has_more_than_2_sales_nominals": post_data.get(
            "has_more_than_2_sales_nominals_enabled", "Yes"
        )
        == "Yes",
        "has_more_than_2_cos_nominals": post_data.get(
            "has_more_than_2_cos_nominals_enabled", "Yes"
        )
        == "Yes",
        "has_more_than_10_overhead_nominals": post_data.get(
            "has_more_than_10_overhead_nominals_enabled", "Yes"
        )
        == "Yes",
        "has_more_than_20_customers": post_data.get(
            "has_more_than_20_customers_enabled", "Yes"
        )
        == "Yes",
        "has_more_than_20_suppliers": post_data.get(
            "has_more_than_20_suppliers_enabled", "Yes"
        )
        == "Yes",
        "consistent_cost_base": post_data.get("consistent_cost_base_enabled", "Yes")
        == "Yes",
        "debtor_days_calculated": post_data.get("debtor_days_calculated_enabled", "Yes")
        == "Yes",
        "creditor_days_calculated": post_data.get(
            "creditor_days_calculated_enabled", "Yes"
        )
        == "Yes",
        "stock_days_calculated": post_data.get("stock_days_calculated_enabled", "Yes")
        == "Yes",
        "cash_balance_visible": post_data.get("cash_balance_visible_enabled", "Yes")
        == "Yes",
    }
    kpi_state["suitability_cfg"] = suit_cfg

    # ---- IHT config ----
    iht_cfg: Dict[str, Any] = {}
    iht_cfg["enabled"] = post_data.get("iht_enabled", "Yes") == "Yes"
    try:
        iht_cfg["threshold"] = int(post_data.get("iht_threshold", "900000"))
    except (TypeError, ValueError):
        iht_cfg["threshold"] = 900000
    kpi_state["iht_cfg"] = iht_cfg

    # ---- Readiness config ----
    readiness_cfg = {
        "is_ebitda_positive": post_data.get(
            "readiness_is_ebitda_positive_enabled", "Yes"
        )
        == "Yes",
        "is_ebitda_more_than_ly": post_data.get(
            "readiness_is_ebitda_more_than_ly_enabled", "Yes"
        )
        == "Yes",
        "has_dividend_last_12m": post_data.get(
            "readiness_has_dividend_last_12m_enabled", "Yes"
        )
        == "Yes",
        "is_dividend_at_least_equal_ly": post_data.get(
            "readiness_is_dividend_at_least_equal_ly_enabled", "Yes"
        )
        == "Yes",
        "is_cash_balance_positive": post_data.get(
            "readiness_is_cash_balance_positive_enabled", "Yes"
        )
        == "Yes",
        "is_cash_more_than_ly": post_data.get(
            "readiness_is_cash_more_than_ly_enabled", "Yes"
        )
        == "Yes",
        "are_sales_improving": post_data.get(
            "readiness_are_sales_improving_enabled", "Yes"
        )
        == "Yes",
    }
    kpi_state["readiness_cfg"] = readiness_cfg

    # ---- Targets for Discussion ----
    def _to_int_0_100(v, default):
        try:
            x = int(v)
        except (TypeError, ValueError):
            x = default
        return max(0, min(100, x))

    def _round10(x):
        return int(round(x / 10.0) * 10)

    targets = (kpi_state.get("targets") or {}).copy()

    if "target_suitability" in post_data:
        targets["suitability"] = _to_int_0_100(post_data.get("target_suitability"), 50)
    if "target_opportunity" in post_data:
        targets["opportunity"] = _to_int_0_100(post_data.get("target_opportunity"), 50)
    if "target_readiness" in post_data:
        targets["readiness"] = _to_int_0_100(post_data.get("target_readiness"), 50)

    for k in ("suitability", "opportunity", "readiness"):
        if k in targets and targets[k] is not None:
            targets[k] = max(0, min(100, _round10(targets[k])))

    kpi_state["targets"] = targets

    # ---- Save ----
    # criteria.kpi_state = kpi_state
    # criteria.opportunity_score = opportunity_score
    # criteria.save()
    if session is not None:
        session[SESSION_KEY_TMPL.format(client_id=client_id)] = kpi_state
        session.modified = True

    return opportunity_score, kpi_state


# -----------------------------
# GET
# -----------------------------


def _score_from_state(saved_state: dict):
    crit = (saved_state or {}).get("criteria") or {}
    enabled = 0
    yes = 0
    for _, v in crit.items():
        if v.get("enabled"):
            enabled += 1
            if str(v.get("flag", "")).strip().lower() == "yes":
                yes += 1
    return round(100 * yes / enabled) if enabled else 0


def get_client_summary_context(
    client_id: int, saved_state: Optional[dict] = None
) -> Dict[str, Any]:

    saved_state = saved_state or {}
    """
    کل منطق GET قبلی view را به context تبدیل می‌کند.
    """
    # Utilities / R&D
    utilities_flag = _get_client_utilities(client_id)
    rd_flag = _get_client_rd(client_id)
    if isinstance(rd_flag, dict):
        rd_flag = rd_flag.get("rd_flag")

    if isinstance(utilities_flag, dict):
        utilities_flag = utilities_flag.get("has_utilities")

    # KPI
    kpi = _get_client_kpi(client_id)
    if kpi is None:
        raise Http404("Client KPI not found")

    # Suitability
    suitability = _get_client_suitability(client_id)

    def _is_yes(v):
        return str(v).strip().lower() == "yes"

    # saved_state = criteria.kpi_state or {}
    saved_suit_cfg = saved_state.get("suitability_cfg", {}) or {}

    suitability_fields = [
        {
            "key": "is_24_month_history",
            "label": "24 Months History",
            "status": "is_24_month_history",
            "value": "CNT_months_with_sales_24",
        },
        {
            "key": "has_more_than_2_sales_nominals",
            "label": "More Than 2 Sales Nominals",
            "status": "has_more_than_2_sales_nominals",
            "value": "CNT_sales_nominals_24",
        },
        {
            "key": "has_more_than_2_cos_nominals",
            "label": "More Than 2 COS Nominals",
            "status": "has_more_than_2_cos_nominals",
            "value": "CNT_cos_nominals_24",
        },
        {
            "key": "has_more_than_10_overhead_nominals",
            "label": "More Than 10 Overhead Nominals",
            "status": "has_more_than_10_overhead_nominals",
            "value": "CNT_overhead_nominals_24",
        },
        {
            "key": "has_more_than_20_customers",
            "label": "More Than 20 Customers",
            "status": "has_more_than_20_customers",
            "value": "CNT_customers_24",
        },
        {
            "key": "has_more_than_20_suppliers",
            "label": "More Than 20 Suppliers",
            "status": "has_more_than_20_suppliers",
            "value": "CNT_suppliers_24",
        },
        {
            "key": "consistent_cost_base",
            "label": "Consistent Cost Base",
            "status": "consistent_cost_base",
            "value": "CNT_inconsistent_months_12",
        },
        {
            "key": "debtor_days_calculated",
            "label": "Debtor Days Calculated",
            "status": "debtor_days_calculated",
            "value": "CNT_debtor_months",
        },
        {
            "key": "creditor_days_calculated",
            "label": "Creditor Days Calculated",
            "status": "creditor_days_calculated",
            "value": "CNT_creditor_months",
        },
        {
            "key": "stock_days_calculated",
            "label": "Stock Days Calculated",
            "status": "stock_days_calculated",
            "value": "CNT_stock_months",
        },
        {
            "key": "cash_balance_visible",
            "label": "Cash Balance Visible",
            "status": "cash_balance_visible",
            "value": "CNT_cash_months",
        },
    ]

    suitability_config_rows = []
    for f in suitability_fields:
        key = f["key"]
        enabled = saved_suit_cfg.get(key, True)
        status_val = (suitability or {}).get(f["status"])
        status = _is_yes(status_val)
        display_value = (suitability or {}).get(f["value"], "")
        suitability_config_rows.append(
            {
                "key": key,
                "label": f["label"],
                "enabled": enabled,
                "display_value": display_value,
                "status": status,
            }
        )

    suitability_top_rows = []
    suitability_bottom_rows = []
    suitability_score = None

    if suitability:

        def yn(field):
            return _is_yes(suitability.get(field))

        suitability_top_rows = [
            {
                "key": "is_24_month_history",
                "label": "24 Months History",
                "value": yn("is_24_month_history"),
            },
            {
                "key": "has_more_than_2_sales_nominals",
                "label": "More Than 2 Sales Nominals",
                "value": yn("has_more_than_2_sales_nominals"),
            },
            {
                "key": "has_more_than_2_cos_nominals",
                "label": "More Than 2 COS Nominals",
                "value": yn("has_more_than_2_cos_nominals"),
            },
            {
                "key": "has_more_than_10_overhead_nominals",
                "label": "More Than 10 Overhead Nominals",
                "value": yn("has_more_than_10_overhead_nominals"),
            },
            {
                "key": "has_more_than_20_customers",
                "label": "More Than 20 Customers",
                "value": yn("has_more_than_20_customers"),
            },
            {
                "key": "has_more_than_20_suppliers",
                "label": "More Than 20 Suppliers",
                "value": yn("has_more_than_20_suppliers"),
            },
        ]
        suitability_bottom_rows = [
            {
                "key": "consistent_cost_base",
                "label": "Consistent Cost Base",
                "value": yn("consistent_cost_base"),
            },
            {
                "key": "debtor_days_calculated",
                "label": "Debtor Days Calculated",
                "value": yn("debtor_days_calculated"),
            },
            {
                "key": "creditor_days_calculated",
                "label": "Creditor Days Calculated",
                "value": yn("creditor_days_calculated"),
            },
            {
                "key": "stock_days_calculated",
                "label": "Stock Days Calculated",
                "value": yn("stock_days_calculated"),
            },
            {
                "key": "cash_balance_visible",
                "label": "Cash Balance Visible",
                "value": yn("cash_balance_visible"),
            },
        ]

        all_flags = suitability_top_rows + suitability_bottom_rows
        enabled_flags = [r for r in all_flags if saved_suit_cfg.get(r["key"], True)]
        enabled_total = len(enabled_flags)
        enabled_yes = sum(1 for r in enabled_flags if r["value"])
        suitability_score = (
            round(100 * enabled_yes / enabled_total) if enabled_total else None
        )

    # IHT (based on kpi)
    saved_iht_cfg = saved_state.get("iht_cfg", {}) or {}
    iht_enabled = saved_iht_cfg.get("enabled", True)
    iht_threshold = saved_iht_cfg.get("threshold", 900000)
    iht_multiple = 3
    ebitda_ty = kpi.get("ebitda_TY") or 0
    try:
        est_value = float(ebitda_ty) * float(iht_multiple)
    except Exception:
        est_value = 0
    iht_flag = "Yes" if (iht_enabled and est_value >= iht_threshold) else "No"

    # Readiness
    readiness = _get_client_readiness(client_id)
    readiness_top_rows = []
    readiness_bottom_rows = []
    readiness_score = None

    saved_read_cfg = saved_state.get("readiness_cfg", {}) or {}

    readiness_config_groups = []
    readiness_config_rows = []

    if readiness:

        def yn_r(field):
            return _is_yes(readiness.get(field))

        readiness_top_rows = [
            {
                "key": "is_ebitda_positive",
                "label": "Is The Client's EBITDA Positive?",
                "value": yn_r("is_ebitda_positive"),
            },
            {
                "key": "is_ebitda_more_than_ly",
                "label": "Is The EBITDA More Than Last Year?",
                "value": yn_r("is_ebitda_more_than_ly"),
            },
            {
                "key": "has_dividend_last_12m",
                "label": "Have They Paid A Dividend In The Last 12 Months?",
                "value": yn_r("has_dividend_last_12m"),
            },
            {
                "key": "is_dividend_at_least_equal_ly",
                "label": "Is The Dividend At Least Equal To Last Year?",
                "value": yn_r("is_dividend_at_least_equal_ly"),
            },
        ]
        readiness_bottom_rows = [
            {
                "key": "is_cash_balance_positive",
                "label": "Is The Cash Balance Positive?",
                "value": yn_r("is_cash_balance_positive"),
            },
            {
                "key": "is_cash_more_than_ly",
                "label": "Is The Cash Balance More Than Last Year?",
                "value": yn_r("is_cash_more_than_ly"),
            },
            {
                "key": "are_sales_improving",
                "label": "Are Sales Improving?",
                "value": yn_r("are_sales_improving"),
            },
        ]

        all_r_flags = readiness_top_rows + readiness_bottom_rows
        enabled_r_flags = [r for r in all_r_flags if saved_read_cfg.get(r["key"], True)]
        enabled_r_total = len(enabled_r_flags)
        enabled_r_yes = sum(1 for r in enabled_r_flags if r["value"])
        readiness_score = (
            round(100 * enabled_r_yes / enabled_r_total) if enabled_r_total else None
        )

        readiness_config_groups = [
            {
                "key": "ebitda",
                "label": "EBITDA",
                "ty": readiness.get("val_ebitda_TY"),
                "ly": readiness.get("val_ebitda_LY"),
                "vs": readiness.get("val_ebitda_vs_ly"),
                "metrics": [
                    {
                        "key": "is_ebitda_positive",
                        "label": "Is The Client's EBITDA Positive?",
                        "status": _is_yes(readiness.get("is_ebitda_positive")),
                        "enabled": saved_read_cfg.get("is_ebitda_positive", True),
                        "enabled_name": "readiness_is_ebitda_positive_enabled",
                    },
                    {
                        "key": "is_ebitda_more_than_ly",
                        "label": "Is The EBITDA More Than Last Year?",
                        "status": _is_yes(readiness.get("is_ebitda_more_than_ly")),
                        "enabled": saved_read_cfg.get("is_ebitda_more_than_ly", True),
                        "enabled_name": "readiness_is_ebitda_more_than_ly_enabled",
                    },
                ],
            },
            {
                "key": "dividend",
                "label": "Dividend",
                "ty": readiness.get("val_dividend_TY"),
                "ly": readiness.get("val_dividend_LY"),
                "vs": readiness.get("val_dividend_vs_ly"),
                "metrics": [
                    {
                        "key": "has_dividend_last_12m",
                        "label": "Have They Paid A Dividend In The Last 12 Months?",
                        "status": _is_yes(readiness.get("has_dividend_last_12m")),
                        "enabled": saved_read_cfg.get("has_dividend_last_12m", True),
                        "enabled_name": "readiness_has_dividend_last_12m_enabled",
                    },
                    {
                        "key": "is_dividend_at_least_equal_ly",
                        "label": "Is The Dividend At Least Equal To Last Year?",
                        "status": _is_yes(
                            readiness.get("is_dividend_at_least_equal_ly")
                        ),
                        "enabled": saved_read_cfg.get(
                            "is_dividend_at_least_equal_ly", True
                        ),
                        "enabled_name": "readiness_is_dividend_at_least_equal_ly_enabled",
                    },
                ],
            },
            {
                "key": "cash",
                "label": "Cash",
                "ty": readiness.get("val_cash_TY"),
                "ly": readiness.get("val_cash_LY"),
                "vs": readiness.get("val_cash_vs_ly"),
                "metrics": [
                    {
                        "key": "is_cash_balance_positive",
                        "label": "Is The Cash Balance Positive?",
                        "status": _is_yes(readiness.get("is_cash_balance_positive")),
                        "enabled": saved_read_cfg.get("is_cash_balance_positive", True),
                        "enabled_name": "readiness_is_cash_balance_positive_enabled",
                    },
                    {
                        "key": "is_cash_more_than_ly",
                        "label": "Is The Cash Balance More Than Last Year?",
                        "status": _is_yes(readiness.get("is_cash_more_than_ly")),
                        "enabled": saved_read_cfg.get("is_cash_more_than_ly", True),
                        "enabled_name": "readiness_is_cash_more_than_ly_enabled",
                    },
                ],
            },
            {
                "key": "sales",
                "label": "Sales",
                "ty": readiness.get("val_revenue_TY"),
                "ly": readiness.get("val_revenue_LY"),
                "vs": readiness.get("val_revenue_vs_ly"),
                "metrics": [
                    {
                        "key": "are_sales_improving",
                        "label": "Are Sales Improving?",
                        "status": _is_yes(readiness.get("are_sales_improving")),
                        "enabled": saved_read_cfg.get("are_sales_improving", True),
                        "enabled_name": "readiness_are_sales_improving_enabled",
                    },
                ],
            },
        ]

        for g in readiness_config_groups:
            for m in g["metrics"]:
                readiness_config_rows.append(
                    {
                        "field": m["label"],
                        "status": m["status"],
                        "enabled": m["enabled"],
                        "enabled_name": f"readiness_{m['key']}_enabled",
                        "ty": g.get("ty"),
                        "ly": g.get("ly"),
                        "vs": g.get("vs"),
                    }
                )

    # Target for Discussion
    targets = (saved_state.get("targets") or {}).copy()
    # opportunity_score = criteria.opportunity_score
    opportunity_score = _score_from_state(saved_state)

    if targets.get("suitability") is None:
        targets["suitability"] = _round10_or_none(suitability_score) or 50
    if targets.get("opportunity") is None:
        targets["opportunity"] = _round10_or_none(opportunity_score) or 50
    if targets.get("readiness") is None:
        targets["readiness"] = _round10_or_none(readiness_score) or 50

    target_suitability = targets["suitability"]
    target_opportunity = targets["opportunity"]
    target_readiness = targets["readiness"]

    if (
        suitability_score is None
        or opportunity_score is None
        or readiness_score is None
    ):
        target_for_discussion = "—"
    else:
        target_for_discussion = (
            "Yes"
            if (
                suitability_score >= target_suitability
                and opportunity_score >= target_opportunity
                and readiness_score >= target_readiness
            )
            else "No"
        )

    # KPI tables
    left_rows = []

    # Revenue vs Last Year
    rev_var = None
    if kpi.get("revenue_TY") is not None and kpi.get("revenue_LY") is not None:
        rev_var = kpi["revenue_TY"] - kpi["revenue_LY"]
    left_rows.append(
        {
            "label": "Revenue vs Last Year",
            "ty": kpi.get("revenue_TY"),
            "ly": kpi.get("revenue_LY"),
            "var": rev_var,
            "is_percentage": False,
        }
    )

    # Gross Margin % vs Last Year
    left_rows.append(
        {
            "label": "Gross Margin % vs Last Year",
            "ty": kpi.get("gross_margin_pct_TY"),
            "ly": kpi.get("gross_margin_pct_LY"),
            "var": kpi.get("gross_margin_vs_LY_pct"),
            "is_percentage": True,
        }
    )

    # Overhead £ vs Last Year
    ovh_var = None
    if kpi.get("overheads_TY") is not None and kpi.get("overheads_LY") is not None:
        ovh_var = kpi["overheads_TY"] - kpi["overheads_LY"]
    left_rows.append(
        {
            "label": "Overhead £ vs Last Year",
            "ty": kpi.get("overheads_TY"),
            "ly": kpi.get("overheads_LY"),
            "var": ovh_var,
            "is_percentage": False,
        }
    )

    # Overhead % vs Last Year
    left_rows.append(
        {
            "label": "Overhead % vs Last Year",
            "ty": kpi.get("overheads_vs_LY_pct"),
            "ly": None,
            "var": kpi.get("overheads_vs_LY_pct"),
            "is_percentage": True,
        }
    )

    # EBITDA vs Last Year
    left_rows.append(
        {
            "label": "EBITDA vs Last Year",
            "ty": kpi.get("ebitda_TY"),
            "ly": kpi.get("ebitda_LY"),
            "var": kpi.get("ebitda_vs_LY_value"),
            "is_percentage": False,
        }
    )

    # EBITDA % vs Last Year
    left_rows.append(
        {
            "label": "EBITDA % vs Last Year",
            "ty": kpi.get("ebitda_pct_TY"),
            "ly": kpi.get("ebitda_pct_LY"),
            "var": kpi.get("ebitda_pct_vs_LY"),
            "is_percentage": True,
        }
    )

    right_rows = []
    right_rows.append(
        {
            "label": "Cash Position (vs Last Year)",
            "ty": kpi.get("cash_position_TY"),
            "ly": kpi.get("cash_position_LY"),
            "var": kpi.get("cash_position_vs_LY"),
            "is_percentage": False,
        }
    )
    right_rows.append(
        {
            "label": "Debtor Days (vs Last Year)",
            "ty": kpi.get("debtor_days_TY"),
            "ly": kpi.get("debtor_days_LY"),
            "var": kpi.get("debtor_days_vs_LY"),
            "is_percentage": False,
        }
    )
    right_rows.append(
        {
            "label": "Creditor Days (vs Last Year)",
            "ty": kpi.get("creditor_days_TY"),
            "ly": kpi.get("creditor_days_LY"),
            "var": kpi.get("creditor_days_vs_LY"),
            "is_percentage": False,
        }
    )
    right_rows.append(
        {
            "label": "Stock Days (vs Last Year)",
            "ty": kpi.get("stock_days_TY"),
            "ly": kpi.get("stock_days_LY"),
            "var": None,
            "is_percentage": False,
        }
    )

    div_var = None
    if kpi.get("dividend_TY") is not None and kpi.get("dividend_LY") is not None:
        div_var = kpi["dividend_TY"] - kpi["dividend_LY"]
    right_rows.append(
        {
            "label": "Dividend (TY / LY)",
            "ty": kpi.get("dividend_TY"),
            "ly": kpi.get("dividend_LY"),
            "var": div_var,
            "is_percentage": False,
        }
    )

    for row in left_rows:
        row["var_class"] = _var_class(row.get("var"))
    for row in right_rows:
        row["var_class"] = _var_class(row.get("var"))

    # Sales trend
    sales_trend = _get_sales_trend(client_id) or []

    # context final
    context = {
        "client_name": kpi.get("client_name"),
        "client_id": kpi.get("client_id"),
        "left_rows": left_rows,
        "right_rows": right_rows,
        "opportunity_score": opportunity_score,
        # suitability
        "suitability_top_rows": suitability_top_rows,
        "suitability_bottom_rows": suitability_bottom_rows,
        "suitability_score": suitability_score,
        "suitability_config_rows": suitability_config_rows,
        # readiness
        "readiness_top_rows": readiness_top_rows,
        "readiness_bottom_rows": readiness_bottom_rows,
        "readiness_score": readiness_score,
        "readiness_config_rows": readiness_config_rows,
        "readiness_config_groups": readiness_config_groups,
        # sales chart
        "sales_trend": sales_trend,
        # state for template
        "kpi_state": saved_state,
        # IHT
        "iht_enabled": iht_enabled,
        "iht_threshold": iht_threshold,
        "iht_multiple": iht_multiple,
        "iht_ebitda_ty": ebitda_ty,
        "iht_est_value": est_value,
        "iht_flag": iht_flag,
        # Utilities / R&D
        "utilities_flag": utilities_flag,
        "rd_flag": rd_flag,
        # Target for Discussion
        "target_suitability": target_suitability,
        "target_opportunity": target_opportunity,
        "target_readiness": target_readiness,
        "target_for_discussion": target_for_discussion,
    }

    return context
