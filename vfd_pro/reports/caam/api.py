from django.db import connection
from django.shortcuts import render, redirect
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from vfd_pro.common.utils import format_month_year

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import connection
import json

import logging

from vfd_pro.common.utils import _fmt_num, fmt_percent
from .selectors import (
    _call_revenue_profitability_sp,
    _call_gm_profitability_sp,
    _call_overhead_profitability_sp,
    _call_overhead_pct_profitability_sp,
    _call_ebitda_profitability_sp,
    _call_newcust_profitability_sp,
    _call_retention_profitability_sp,
    _call_cash_position_profitability_sp,
    _call_debtor_days_profitability_sp,
    _call_creditor_days_profitability_sp,
    _call_stock_days_profitability_sp,
    _get_caam_report,
)

sp_logger = logging.getLogger("sp_logger")


@require_GET
def ajax_caam_report(request, company_id: int):
    try:
        rows = _get_caam_report(company_id)
        for r in rows:
            r["reporting_month_label"] = format_month_year(r.get("reporting_date"))

        return JsonResponse({"ok": True, "rows": rows})
    except Exception as e:
        sp_logger.error(f"ajax_caam_report ERROR: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_revenue_criteria(request, client_id: int):
    print("### ajax_revenue_criteria HIT ###")

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_revenue_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:

        rev_enabled = request.POST["rev_enabled"]  # 'Yes' / 'No'
        rev_period_str = request.POST.get("rev_period", "12")
        rev_dir = request.POST["rev_dir"]  # '+/-', '+', '-'
        rev_threshold_str = request.POST["rev_threshold"]  # Ex: "15.00"

        sp_logger.debug(
            f"FORM FIELDS => rev_enabled={rev_enabled}, "
            f"rev_period={rev_period_str}, rev_dir={rev_dir}, "
            f"rev_threshold={rev_threshold_str}"
        )

        # val_adj
        try:
            val_adj = int(request.POST.get("val_adj", 3))
        except (TypeError, ValueError):
            val_adj = 3

        # parse period
        try:
            rev_period = int(rev_period_str)
        except ValueError:
            sp_logger.error(f"Invalid rev_period: {rev_period_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid rev_period"}, status=400
            )

        # parse threshold
        try:
            rev_threshold = Decimal(rev_threshold_str)
        except Exception:
            sp_logger.error(f"Invalid rev_threshold: {rev_threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid rev_threshold"}, status=400
            )

        rev_min_months = None

        sp_logger.debug(
            "CALLING _call_revenue_profitability_sp WITH => "
            f"client_id={client_id}, period={rev_period}, rev_dir={rev_dir}, "
            f"min_months={rev_min_months}, threshold={rev_threshold}, enabled={rev_enabled}"
        )

        result = _call_revenue_profitability_sp(
            client_id=client_id,
            period=rev_period,
            sign_mode=rev_dir,
            min_months=rev_min_months,
            threshold=rev_threshold,
            flag_on=rev_enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for Revenue.")
            return JsonResponse(
                {"ok": False, "error": "No result from stored procedure"},
                status=200,
            )

        profit_impact = result.get("Impact_Profit_Revenue")
        val_impact = (profit_impact * val_adj) if profit_impact is not None else None

        data = {
            "ok": True,
            "rev_last_12": fmt_percent(result.get("Revenue_vs_LY_12m_pct"), 1),
            "rev_last_6": fmt_percent(result.get("Revenue_vs_LY_6m_pct"), 1),
            "rev_last_3": fmt_percent(result.get("Revenue_vs_LY_3m_pct"), 1),
            "rev_flag": (
                str(result.get("Revenue_Flag"))
                if result.get("Revenue_Flag") is not None
                else None
            ),
            "rev_profit_impact": _fmt_num(profit_impact, 1),
            "rev_val_impact": _fmt_num(val_impact, 1),
            "val_adj": val_adj,
        }

        sp_logger.debug(f"JSON RESPONSE DATA (Revenue) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (Revenue): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"},
            status=400,
        )
    except Exception as e:
        sp_logger.error(
            f"UNEXPECTED ERROR in ajax_revenue_criteria: {e}", exc_info=True
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_gm_criteria(request, client_id: int):
    print("### ajax_gm_criteria HIT ###")

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_gm_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:

        gm_enabled = request.POST["gm_enabled"]  # 'Yes' / 'No'
        gm_period_str = request.POST.get("gm_period", "12")
        gm_dir = request.POST["gm_dir"]  # '+', '-', '+/-'
        gm_threshold_str = request.POST["gm_threshold"]  # "10.00"

        sp_logger.debug(
            f"FORM FIELDS => gm_enabled={gm_enabled}, "
            f"gm_period={gm_period_str}, gm_dir={gm_dir}, "
            f"gm_threshold={gm_threshold_str}"
        )

        # val_adj
        try:
            val_adj = int(request.POST.get("val_adj", 3))
        except (TypeError, ValueError):
            val_adj = 3

        # parse period
        try:
            gm_period = int(gm_period_str)
        except ValueError:
            sp_logger.error(f"Invalid gm_period: {gm_period_str}")
            return JsonResponse({"ok": False, "error": "Invalid gm_period"}, status=400)

        # parse threshold
        try:
            gm_threshold = Decimal(gm_threshold_str)
        except Exception:
            sp_logger.error(f"Invalid gm_threshold: {gm_threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid gm_threshold"}, status=400
            )

        gm_min_months = None

        sp_logger.debug(
            "CALLING _call_gm_profitability_sp WITH => "
            f"client_id={client_id}, period={gm_period}, gm_dir={gm_dir}, "
            f"min_months={gm_min_months}, threshold={gm_threshold}, enabled={gm_enabled}"
        )

        result = _call_gm_profitability_sp(
            client_id=client_id,
            period=gm_period,
            sign_mode=gm_dir,
            min_months=gm_min_months,
            threshold=gm_threshold,
            flag_on=gm_enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for Gross Margin.")
            return JsonResponse(
                {"ok": False, "error": "No result from stored procedure"},
                status=200,
            )

        gm_profit_impact = result.get("Impact_Profit_GM")
        gm_val_impact = (
            (gm_profit_impact * val_adj) if gm_profit_impact is not None else None
        )

        data = {
            "ok": True,
            "gm_last_12": fmt_percent(result.get("gm_pct_vs_ly_12m"), 1),
            "gm_last_6": fmt_percent(result.get("gm_pct_vs_ly_6m"), 1),
            "gm_last_3": fmt_percent(result.get("gm_pct_vs_ly_3m"), 1),
            "gm_flag": (
                str(result.get("Gross_Margin_Flag"))
                if result.get("Gross_Margin_Flag") is not None
                else None
            ),
            "gm_profit_impact": _fmt_num(gm_profit_impact, 1),
            "gm_val_impact": _fmt_num(gm_val_impact, 1),
            "val_adj": val_adj,
        }

        sp_logger.debug(f"JSON RESPONSE DATA (Gross Margin) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (Gross Margin): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"},
            status=400,
        )
    except Exception as e:
        sp_logger.error(f"UNEXPECTED ERROR in ajax_gm_criteria: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_oh_val_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_oh_val_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        oh_enabled = request.POST["oh_val_enabled"]  # 'Yes' / 'No'
        oh_period_str = request.POST.get("oh_val_period", "12")
        oh_dir = request.POST["oh_val_dir"]  # '+', '-', '+/-'
        oh_threshold_str = request.POST["oh_val_threshold"]  #  "10.00"

        sp_logger.debug(
            f"FORM FIELDS => oh_val_enabled={oh_enabled}, "
            f"oh_val_period={oh_period_str}, oh_val_dir={oh_dir}, "
            f"oh_val_threshold={oh_threshold_str}"
        )

        val_adj = int(request.POST.get("val_adj", 3))

        try:
            val_adj = int(request.POST.get("val_adj", 3))
        except (TypeError, ValueError):
            val_adj = 3

        try:
            oh_period = int(oh_period_str)
        except ValueError:
            sp_logger.error(f"Invalid oh_val_period: {oh_period_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid oh_val_period"}, status=400
            )

        try:
            oh_threshold = Decimal(oh_threshold_str)
        except Exception:
            sp_logger.error(f"Invalid oh_val_threshold: {oh_threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid oh_val_threshold"}, status=400
            )

        oh_min_months = None

        sp_logger.debug(
            "CALLING _call_overhead_profitability_sp WITH => "
            f"client_id={client_id}, period={oh_period}, oh_dir={oh_dir}, "
            f"min_months={oh_min_months}, threshold={oh_threshold}, enabled={oh_enabled}"
        )

        result = _call_overhead_profitability_sp(
            client_id=client_id,
            period=oh_period,
            sign_mode=oh_dir,
            min_months=oh_min_months,
            threshold=oh_threshold,
            flag_on=oh_enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for Overhead.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        profit_impact = result.get("Profit_Impact_Overheads")
        val_impact = (profit_impact * val_adj) if profit_impact is not None else None

        data = {
            "ok": True,
            "oh_val_last_12": fmt_percent(result.get("Overheads_vs_LY_12m_pct"), 1),
            "oh_val_last_6": fmt_percent(result.get("Overheads_vs_LY_6m_pct"), 1),
            "oh_val_last_3": fmt_percent(result.get("Overheads_vs_LY_3m_pct"), 1),
            "oh_val_flag": (
                str(result.get("Overheads_Flag"))
                if result.get("Overheads_Flag") is not None
                else None
            ),
            "oh_val_profit_impact": _fmt_num(profit_impact, 1),
            "oh_val_val_impact": _fmt_num(val_impact, 1),
            "val_adj": val_adj,
        }

        sp_logger.debug(f"JSON RESPONSE DATA (Overhead) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (Overhead): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(f"UNEXPECTED ERROR in ajax_oh_val_criteria: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_oh_pct_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_oh_pct_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        oh_enabled = request.POST["oh_pct_enabled"]  # 'Yes' / 'No'
        oh_period_str = request.POST.get("oh_pct_period", "12")
        oh_dir = request.POST["oh_pct_dir"]  # '+', '-', '+/-'
        oh_threshold_str = request.POST["oh_pct_threshold"]  # "10.00"
        val_adj = int(request.POST.get("val_adj", 3))

        try:
            val_adj = int(request.POST.get("val_adj", 3))
        except (TypeError, ValueError):
            val_adj = 3

        sp_logger.debug(
            f"FORM FIELDS => oh_pct_enabled={oh_enabled}, "
            f"oh_pct_period={oh_period_str}, oh_pct_dir={oh_dir}, "
            f"oh_pct_threshold={oh_threshold_str}"
        )

        try:
            oh_period = int(oh_period_str)
        except ValueError:
            sp_logger.error(f"Invalid oh_pct_period: {oh_period_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid oh_pct_period"}, status=400
            )

        try:
            oh_threshold = Decimal(oh_threshold_str)
        except Exception:
            sp_logger.error(f"Invalid oh_pct_threshold: {oh_threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid oh_pct_threshold"}, status=400
            )

        oh_min_months = None

        sp_logger.debug(
            "CALLING _call_overhead_pct_profitability_sp WITH => "
            f"client_id={client_id}, period={oh_period}, oh_dir={oh_dir}, "
            f"min_months={oh_min_months}, threshold={oh_threshold}, enabled={oh_enabled}"
        )

        result = _call_overhead_pct_profitability_sp(
            client_id=client_id,
            period=oh_period,
            sign_mode=oh_dir,
            min_months=oh_min_months,
            threshold=oh_threshold,
            flag_on=oh_enabled,
        )

        sp_logger.debug(f"RESULT KEYS => {list(result.keys())}")
        sp_logger.debug(f"RESULT => {result}")

        sp_logger.debug(f"SP RAW RESULT (dict, Overhead %) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for Overhead %.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        profit_impact = result.get("Profit_Impact_Overhead_pct")
        val_impact = (profit_impact * val_adj) if profit_impact is not None else None

        data = {
            "ok": True,
            "oh_pct_last_12": fmt_percent(result.get("Overhead_pct_vs_LY_12m"), 1),
            "oh_pct_last_6": fmt_percent(result.get("Overhead_pct_vs_LY_6m"), 1),
            "oh_pct_last_3": fmt_percent(result.get("Overhead_pct_vs_LY_3m"), 1),
            "oh_pct_flag": (
                str(result.get("Overhead_pct_Flag"))
                if result.get("Overhead_pct_Flag") is not None
                else None
            ),
            "oh_pct_profit_impact": _fmt_num(profit_impact, 1),
            "oh_pct_val_impact": _fmt_num(val_impact, 1),
            "val_adj": val_adj,
        }

        sp_logger.debug(f"JSON RESPONSE DATA (Overhead %) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (Overhead %): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(f"UNEXPECTED ERROR in ajax_oh_pct_criteria: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_ebitda_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_ebitda_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        e_enabled = request.POST["ebitda_enabled"]  # 'Yes' / 'No'
        e_period_str = request.POST.get("ebitda_period", "12")  # "3" / "6" / "12" )
        e_dir = request.POST["ebitda_dir"]  # '+', '-', '+/-'
        e_threshold_str = request.POST["ebitda_threshold"]  # "10.00"

        sp_logger.debug(
            f"FORM FIELDS => ebitda_enabled={e_enabled}, "
            f"ebitda_period={e_period_str}, ebitda_dir={e_dir}, "
            f"ebitda_threshold={e_threshold_str}"
        )

        try:
            e_period = int(e_period_str)
        except ValueError:
            sp_logger.warning(f"Invalid ebitda_period (ignored in SP): {e_period_str}")
            e_period = 12

        try:
            e_threshold = Decimal(e_threshold_str)
        except Exception:
            sp_logger.error(f"Invalid ebitda_threshold: {e_threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid ebitda_threshold"}, status=400
            )

        e_min_months = None

        sp_logger.debug(
            "CALLING _call_ebitda_profitability_sp WITH => "
            f"client_id={client_id}, dir={e_dir}, "
            f"min_months={e_min_months}, threshold={e_threshold}, enabled={e_enabled}"
        )

        result = _call_ebitda_profitability_sp(
            client_id=client_id,
            sign_mode=e_dir,
            min_months=e_min_months,
            threshold=e_threshold,
            flag_on=e_enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (dict, EBITDA) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for EBITDA.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        profit_impact = result.get("EBITDA_Impact")

        data = {
            "ok": True,
            "ebitda_ty": _fmt_num(result.get("EBITDA_TY_12m"), 0),
            "ebitda_ly": _fmt_num(result.get("EBITDA_LY_12m"), 0),
            "ebitda_var_pct": _fmt_num(result.get("EBITDA_vs_LY_12m_pct"), 1),
            "ebitda_var_val": _fmt_num(result.get("EBITDA_vs_LY_12m"), 0),
            "ebitda_flag": (
                str(result.get("EBITDA_Flag"))
                if result.get("EBITDA_Flag") is not None
                else None
            ),
            "ebitda_impact": _fmt_num(profit_impact, 1),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (EBITDA) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (EBITDA): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(f"UNEXPECTED ERROR in ajax_ebitda_criteria: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_newcust_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_newcust_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["newcust_enabled"]
        period_str = request.POST.get("newcust_period", "12")
        direction = request.POST["newcust_dir"]
        threshold_str = request.POST["newcust_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => newcust_enabled={enabled}, "
            f"newcust_period={period_str}, newcust_dir={direction}, "
            f"newcust_threshold={threshold_str}"
        )

        try:
            period = int(period_str)
        except ValueError:
            sp_logger.warning(f"Invalid newcust_period (ignored in SP): {period_str}")
            period = 12

        try:
            threshold = Decimal(threshold_str)
        except Exception:
            sp_logger.error(f"Invalid newcust_threshold: {threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid newcust_threshold"}, status=400
            )

        min_months = None

        result = _call_newcust_profitability_sp(
            client_id=client_id,
            sign_mode=direction,
            min_months=min_months,
            threshold=threshold,
            flag_on=enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (NewCust dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for New Customers.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        data = {
            "ok": True,
            "newcust_ty": _fmt_num(result.get("NewCust_TY"), 0),
            "newcust_ly": _fmt_num(result.get("NewCust_LY"), 0),
            "newcust_var_pct": _fmt_num(result.get("NewCust_Var_pct"), 1),
            "newcust_flag": (
                str(result.get("NewCust_Flag"))
                if result.get("NewCust_Flag") is not None
                else None
            ),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (NewCust) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (NewCust): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(
            f"UNEXPECTED ERROR in ajax_newcust_criteria: {e}", exc_info=True
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_retention_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_retention_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["retention_enabled"]
        period_str = request.POST.get("retention_period", "12")
        direction = request.POST["retention_dir"]
        threshold_str = request.POST["retention_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => retention_enabled={enabled}, "
            f"retention_period={period_str}, retention_dir={direction}, "
            f"retention_threshold={threshold_str}"
        )

        try:
            period = int(period_str)
        except ValueError:
            sp_logger.warning(f"Invalid retention_period (ignored in SP): {period_str}")
            period = 12

        try:
            threshold = Decimal(threshold_str)
        except Exception:
            sp_logger.error(f"Invalid retention_threshold: {threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid retention_threshold"}, status=400
            )

        min_months = None

        result = _call_retention_profitability_sp(
            client_id=client_id,
            sign_mode=direction,
            min_months=min_months,
            threshold=threshold,
            flag_on=enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (Retention dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for Retention.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        # Retention_TY, Retention_LY, Retention_Var_pct, Retention_Flag
        data = {
            "ok": True,
            "retention_ty": _fmt_num(result.get("Retention_TY"), 1),
            "retention_ly": _fmt_num(result.get("Retention_LY"), 1),
            "retention_var_pct": _fmt_num(result.get("Retention_Var_pct"), 1),
            "retention_flag": (
                str(result.get("Retention_Flag"))
                if result.get("Retention_Flag") is not None
                else None
            ),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (Retention) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (Retention): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(
            f"UNEXPECTED ERROR in ajax_retention_criteria: {e}", exc_info=True
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_cash_criteria(request, client_id: int):
    """
    AJAX: Cash Position (Enable / Period / Dir / Threshold)
    SP: sp_vfd_client_cash_position_profitability
    """

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_cash_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["cash_enabled"]
        direction = request.POST["cash_dir"]
        threshold_str = request.POST["cash_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => cash_enabled={enabled}, " f"cash_threshold={threshold_str}"
        )

        try:
            threshold = Decimal(threshold_str)
        except Exception:
            sp_logger.error(f"Invalid cash_threshold: {threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid cash_threshold"}, status=400
            )

        min_months = None

        result = _call_cash_position_profitability_sp(
            client_id=client_id,
            sign_mode=direction,
            min_months=min_months,
            threshold=threshold,
            flag_on=enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (Cash dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for Cash Position.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        data = {
            "ok": True,
            "cash_ty": _fmt_num(result.get("Cash_TY"), 0),
            "cash_ly": _fmt_num(result.get("Cash_LY"), 0),
            "cash_var_pct": fmt_percent(result.get("Cash_vs_LY_pct"), 1),
            "cash_var_val": _fmt_num(result.get("Cash_vs_LY_value"), 0),
            "cash_flag": (
                str(result.get("Cash_Flag"))
                if result.get("Cash_Flag") is not None
                else None
            ),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (Cash) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (Cash): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(f"UNEXPECTED ERROR in ajax_cash_criteria: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_debtordays_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_debtordays_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["debtordays_enabled"]
        direction = request.POST["debtordays_dir"]
        threshold_str = request.POST["debtordays_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => debtordays_enabled={enabled}, "
            f"debtordays_threshold={threshold_str}"
        )

        try:
            threshold = Decimal(threshold_str)
        except Exception:
            sp_logger.error(f"Invalid debtordays_threshold: {threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid debtordays_threshold"}, status=400
            )

        min_months = None

        result = _call_debtor_days_profitability_sp(
            client_id=client_id,
            sign_mode=direction,
            min_months=min_months,
            threshold=threshold,
            flag_on=enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (Debtor dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for DebtorDays.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        data = {
            "ok": True,
            "debtordays_ty": _fmt_num(result.get("DebtorDays_TY"), 0),
            "debtordays_ly": _fmt_num(result.get("DebtorDays_LY"), 0),
            "debtordays_var_pct": fmt_percent(result.get("DebtorDays_Var_pct"), 1),
            "debtordays_var_val": _fmt_num(result.get("DebtorDays_Var_value"), 0),
            "debtordays_flag": (
                str(result.get("DebtorDays_Flag"))
                if result.get("DebtorDays_Flag") is not None
                else None
            ),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (DebtorDays) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (DebtorDays): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(
            f"UNEXPECTED ERROR in ajax_debtordays_criteria: {e}", exc_info=True
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_creditordays_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_creditordays_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["creditordays_enabled"]
        direction = request.POST["creditordays_dir"]
        threshold_str = request.POST["creditordays_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => creditordays_enabled={enabled}, "
            f"creditordays_threshold={threshold_str}"
        )

        try:
            threshold = Decimal(threshold_str)
        except Exception:
            sp_logger.error(f"Invalid creditordays_threshold: {threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid creditordays_threshold"}, status=400
            )

        min_months = None

        result = _call_creditor_days_profitability_sp(
            client_id=client_id,
            sign_mode=direction,
            min_months=min_months,
            threshold=threshold,
            flag_on=enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (Creditor dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for CreditorDays.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        data = {
            "ok": True,
            "creditordays_ty": _fmt_num(result.get("CreditorDays_TY"), 0),
            "creditordays_ly": _fmt_num(result.get("CreditorDays_LY"), 0),
            "creditordays_var_pct": fmt_percent(result.get("CreditorDays_Var_pct"), 1),
            "creditordays_var_val": _fmt_num(result.get("CreditorDays_Var_value"), 0),
            "creditordays_flag": (
                str(result.get("CreditorDays_Flag"))
                if result.get("CreditorDays_Flag") is not None
                else None
            ),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (CreditorDays) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (CreditorDays): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(
            f"UNEXPECTED ERROR in ajax_creditordays_criteria: {e}", exc_info=True
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_stockdays_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_stockdays_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["stockdays_enabled"]
        direction = request.POST["stockdays_dir"]
        threshold_str = request.POST["stockdays_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => stockdays_enabled={enabled}, "
            f"stockdays_threshold={threshold_str}"
        )

        try:
            threshold = Decimal(threshold_str)
        except Exception:
            sp_logger.error(f"Invalid stockdays_threshold: {threshold_str}")
            return JsonResponse(
                {"ok": False, "error": "Invalid stockdays_threshold"}, status=400
            )

        min_months = None

        result = _call_stock_days_profitability_sp(
            client_id=client_id,
            sign_mode=direction,
            min_months=min_months,
            threshold=threshold,
            flag_on=enabled,
        )

        sp_logger.debug(f"SP RAW RESULT (Stock dict) => {result}")

        if not result:
            sp_logger.debug("SP returned NO RESULT for StockDays.")
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

        data = {
            "ok": True,
            "stockdays_ty": _fmt_num(result.get("StockDays_TY"), 0),
            "stockdays_ly": _fmt_num(result.get("StockDays_LY"), 0),
            "stockdays_var_pct": fmt_percent(result.get("StockDays_Var_pct"), 1),
            "stockdays_var_val": _fmt_num(result.get("StockDays_Var_value"), 0),
            "stockdays_flag": (
                str(result.get("StockDays_Flag"))
                if result.get("StockDays_Flag") is not None
                else None
            ),
        }

        sp_logger.debug(f"JSON RESPONSE DATA (StockDays) => {data}")
        return JsonResponse(data)

    except KeyError as e:
        sp_logger.error(f"Missing field in POST (StockDays): {e}", exc_info=True)
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        sp_logger.error(
            f"UNEXPECTED ERROR in ajax_stockdays_criteria: {e}", exc_info=True
        )
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@require_POST
def ajax_save_config(request, client_id: int):
    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_save_config CALLED")
    sp_logger.debug(f"client_id={client_id}")

    raw_body_bytes = request.body or b""
    try:
        raw_body_str = raw_body_bytes.decode("utf-8", errors="replace")
    except Exception:
        raw_body_str = str(raw_body_bytes)

    sp_logger.debug(f"RAW BODY (str) => {raw_body_str}")

    try:
        # 1) Parse JSON
        try:
            payload = json.loads(raw_body_str or "{}")
        except Exception as e:
            sp_logger.error(f"Invalid JSON body: {e}", exc_info=True)
            return JsonResponse({"ok": False, "error": "Invalid JSON body"}, status=400)

        sp_logger.debug(f"PARSED PAYLOAD => {payload}")

        # 2) Extract fields
        company_id = payload.get("company_id")
        version = payload.get("version", 0)
        config = payload.get("config")
        reset_flag = payload.get("reset_flag", 0)
        try:
            reset_flag = int(reset_flag or 0)
        except Exception:
            reset_flag = 0

        sp_logger.debug(
            f"EXTRACTED FIELDS => company_id={company_id}, version={version}, "
            f"config_type={type(config).__name__}"
        )

        # 3) Validate
        if company_id is None:
            sp_logger.error("Validation error: company_id is required")
            return JsonResponse(
                {"ok": False, "error": "company_id is required"}, status=400
            )

        if config is None or not isinstance(config, dict):
            sp_logger.error(
                f"Validation error: config must be a JSON object. Got: {type(config).__name__}"
            )
            return JsonResponse(
                {"ok": False, "error": "config must be a JSON object"}, status=400
            )

        # 4) Normalize version
        try:
            version_float = float(version)
        except Exception:
            sp_logger.error(f"Invalid version value: {version}. Defaulting to 0.0")
            version_float = 0.0

        # 5) Dump config
        try:
            config_json_str = json.dumps(config)
        except Exception as e:
            sp_logger.error(f"Failed to json.dumps(config): {e}", exc_info=True)
            return JsonResponse(
                {"ok": False, "error": "config is not JSON serializable"}, status=400
            )

        sp_logger.debug(
            f"FINAL INPUTS => client_id={client_id}, company_id={company_id}, "
            f"version={version_float}, config_json_len={len(config_json_str)}"
        )
        sp_logger.debug(f"CONFIG JSON => {config_json_str}")

        # 6) Call SP
        with connection.cursor() as cursor:
            sp_logger.debug("Calling SP: sp_caam_save_criteria(...)")

            cursor.execute(
                "CALL sp_caam_save_criteria(%s, %s, %s, %s, %s)",
                [client_id, company_id, version_float, config_json_str, reset_flag],
            )

            row = cursor.fetchone()
            cols = [c[0] for c in cursor.description] if cursor.description else []

            sp_logger.debug(f"SP cursor.description cols => {cols}")
            sp_logger.debug(f"SP fetched row => {row}")

        result = dict(zip(cols, row)) if (row and cols) else None
        sp_logger.debug(f"SP RESULT dict => {result}")

        data = {"ok": True, "row": result}
        sp_logger.debug(f"JSON RESPONSE DATA (ajax_save_config) => {data}")
        return JsonResponse(data)

    except Exception as e:
        sp_logger.error(f"UNEXPECTED ERROR in ajax_save_config: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
