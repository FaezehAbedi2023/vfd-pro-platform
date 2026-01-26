from django.http import Http404
from django.shortcuts import render, redirect

from vfd_pro.reports.caam.selectors import (
    _get_caam_report_details,
    _get_caam_report_config,
    _get_sales_trend,
)

from vfd_pro.reports.caam.services import (
    get_suitability,
    get_suitability_settings,
    get_readiness_settings,
    get_readiness,
    get_performance_kpi,
    get_working_capital_kpi,
    get_iht_settings,
    get_performance_settings,
    get_working_capital_settings,
    build_company_settings_modal_context,
)


def client_assessment(request, company_id: int):
    context = build_company_settings_modal_context(company_id)
    context["defaults_modal"] = build_company_settings_modal_context(0)
    return render(request, "caam/client_assessment.html", context)


def client_summary(request, client_id: int):

    context = {
        "FROM_ASSESSMENT": request.GET.get("from") == "assessment",
    }

    try:
        company_id = int(request.GET.get("company_id") or 0)
    except (TypeError, ValueError):
        company_id = 0

    if not company_id:
        return render(request, "caam/client_summary.html", context)

    cfg = (
        _get_caam_report_config(client_id=client_id)
        or _get_caam_report_config(client_id=0)
        or {}
    )
    context["cfg"] = cfg
    context["p_period_str"] = str(cfg.get("p_period") or "")

    context["sales_trend"] = _get_sales_trend(client_id)

    caam_row = _get_caam_report_details(company_id=company_id, client_id=client_id)
    if caam_row:
        context.update(caam_row)
        context["caam_row"] = caam_row
        context["suitability"] = get_suitability(caam_row)
        context["suitability_settings"] = get_suitability_settings(caam_row, cfg)
        context["readiness_settings"] = get_readiness_settings(caam_row, cfg)
        context["readiness"] = get_readiness(caam_row)
        context["performance_kpi"] = get_performance_kpi(context)
        context["working_capital_kpi"] = get_working_capital_kpi(context)
        context["iht_settings"] = get_iht_settings(caam_row, cfg)
        context["perf_settings"] = get_performance_settings(
            cfg, context, context.get("p_period_str") or ""
        )
        context["working_capital_settings"] = get_working_capital_settings(cfg, context)

    return render(request, "caam/client_summary.html", context)
