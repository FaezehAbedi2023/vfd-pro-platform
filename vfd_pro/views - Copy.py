from datetime import date
from django.db.models import Q
from django.shortcuts import render
from .models import ClientTransaction, OpportunityCriteria
from django.http import HttpResponse
from io import BytesIO
import openpyxl
import os
from .vfd_collect_report_data import get_metrics_from_database, get_derived_metrics
from django.db import connection
from django.http import Http404
from django.shortcuts import render, redirect
import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import logging
from django.db import connection
from decimal import Decimal, ROUND_HALF_UP

sp_logger = logging.getLogger("sp_logger")


def _fmt_num(val, places=1):

    if val is None:
        return None
    try:
        return f"{float(val):.{places}f}"
    except (TypeError, ValueError):
        return str(val)


def fmt_percent(val, places=1):
    if val is None:
        return None
    try:
        return f"{float(val):.{places}f}%"
    except (TypeError, ValueError):
        return str(val)


def call_sp_single_row(sp_name: str, params: list):

    sp_logger.debug("==================================================")
    sp_logger.debug(f"CALL SP: {sp_name}")
    sp_logger.debug(f"INPUT PARAMS: {params}")

    with connection.cursor() as cursor:
        cursor.callproc(sp_name, params)
        row = cursor.fetchone()

        sp_logger.debug(f"RAW OUTPUT ROW: {row}")

        if row is None:
            sp_logger.debug("NO DATA returned from SP.")
            return None, None

        columns = [col[0] for col in cursor.description]
        sp_logger.debug(f"COLUMNS: {columns}")

    return row, columns


def portfolio_view(request):
    qs = ClientTransaction.objects.all()

    # فیلترها از query string
    search = request.GET.get("search", "").strip()

    selected_sources = request.GET.getlist("source")
    selected_categories = request.GET.getlist("category")
    selected_currencies = request.GET.getlist("currency_code")

    year = request.GET.get("year", "")
    month = request.GET.get("month", "")

    if search:
        qs = qs.filter(
            Q(description__icontains=search)
            | Q(source__icontains=search)
            | Q(category__icontains=search)
        )

    if selected_sources:
        qs = qs.filter(source__in=selected_sources)

    if selected_categories:
        qs = qs.filter(category__in=selected_categories)

    if selected_currencies:
        qs = qs.filter(currency_code__in=selected_currencies)

    if year:
        qs = qs.filter(transaction_date__year=year)

    if month:
        try:
            month_int = int(month)
            qs = qs.filter(transaction_date__month=month_int)
        except ValueError:
            pass

    transactions = qs.order_by("-transaction_date", "-id")[:10]

    available_sources = (
        ClientTransaction.objects.exclude(source__isnull=True)
        .exclude(source__exact="")
        .values_list("source", flat=True)
        .distinct()
        .order_by("source")
    )

    available_categories = (
        ClientTransaction.objects.exclude(category__isnull=True)
        .exclude(category__exact="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    available_currencies = (
        ClientTransaction.objects.exclude(currency_code__isnull=True)
        .exclude(currency_code__exact="")
        .values_list("currency_code", flat=True)
        .distinct()
        .order_by("currency_code")
    )

    current_year = date.today().year
    years = list(range(current_year - 5, current_year + 1))

    months = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    context = {
        "transactions": transactions,
        "available_sources": available_sources,
        "available_categories": available_categories,
        "available_currencies": available_currencies,
        "selected_sources": selected_sources,
        "selected_categories": selected_categories,
        "selected_currencies": selected_currencies,
        "search": search,
        "years": years,
        "months": months,
        "selected_year": year,
        "selected_month": month,
    }

    return render(request, "vfd_pro/portfolio.html", context)


def download_vfd_report(request):
    # config از همون environment هایی میاد که تو docker-compose تعریف کردی
    config = {
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "host": os.environ.get("DB_HOST"),
        "port": int(os.environ.get("DB_PORT")),  # "3306" -> 3306
        "database": os.environ.get("DB_NAME"),
    }

    # فعلاً برای تست:
    client_id = 9312  # بعداً می‌تونی از URL یا فرم بگیری

    # ۱) گرفتن متریک‌ها از دیتابیس
    metrics = get_metrics_from_database(config, client_id)
    metrics = get_derived_metrics(metrics)

    # ۲) ساختن فایل Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "VFD Report"

    # هدر
    ws.append(["Metric Name", "Value"])

    # پر کردن دیتای دیکشنری metrics
    for key, value in metrics.items():
        ws.append([key, str(value)])

    # ۳) ذخیره در حافظه و برگرداندن به عنوان فایل دانلودی
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="VFD_Report.xlsx"'
    return response


# ---------- Helperهای دیتابیس ----------


def _get_client_kpi(client_id: int):
    """
    KPIهای اصلی از ویوی vfd_client_kpis
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM vw_vfd_client_kpis WHERE client_id = %s",
            [client_id],
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))


def _get_client_suitability(client_id: int):
    """
    داده‌های Suitability از vfd_client_suitability
    """
    with connection.cursor() as cursor:
        cursor.execute(
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
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))


def _get_client_readiness(client_id: int):
    """
    داده‌های Readiness از vw_vfd_client_readiness
    """
    with connection.cursor() as cursor:
        cursor.execute(
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
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))


def _get_client_utilities(client_id: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT has_utilities
            FROM vw_vfd_client_utilities
            WHERE client_id = %s
            """,
            [client_id],
        )
        row = cursor.fetchone()
        return row[0] if row else "No"


def _get_client_rd(client_id: int) -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rd_flag FROM vw_vfd_client_rd WHERE client_id = %s",
            [client_id],
        )
        row = cursor.fetchone()
        print("DEBUG RD ROW:", row)
        return row[0] if row else "No"


def _get_sales_trend(client_id: int):
    """
    داده‌های نمودار Sales Trend از vfd_client_sales_trend
    ستون‌ها: client_id, offset, sales_month, sales_rolling_12_months
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT offset, sales_month, sales_rolling_12_months
            FROM vfd_client_sales_trend
            WHERE client_id = %s
            ORDER BY offset
            """,
            [client_id],
        )
        rows = cursor.fetchall()
        if not rows:
            return []

        result = []
        for r in rows:
            offset, sales_month, rolling_12 = r
            result.append(
                {
                    "offset": int(offset),
                    "sales_month": float(sales_month),
                    "rolling_12": float(rolling_12),
                }
            )
        return result


def _var_class(value):
    """
    تعیین کلاس رنگ برای ستون Var در جدول KPI
    مثبت → سبز، منفی → قرمز، صفر/None → خنثی
    """
    if value is None:
        return "kpi-var-neutral"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "kpi-var-neutral"
    if v > 0:
        return "kpi-var-positive"
    if v < 0:
        return "kpi-var-negative"
    return "kpi-var-neutral"


# ---------- View  ----------


def _round10_or_none(v):
    if v is None:
        return None

    # v رو حتما Decimal کن (اگر از قبل نبود)
    if not isinstance(v, Decimal):
        v = Decimal(str(v))

    ten = Decimal("10")

    # گرد کردن به نزدیک‌ترین مضرب 10
    return int((v / ten).to_integral_value(rounding=ROUND_HALF_UP) * ten)


def client_summary(request, client_id: int):

    criteria, _ = OpportunityCriteria.objects.get_or_create(client_id=client_id)

    # //Post//////////////////////////////////////
    if request.method == "POST":
        opportunity_score, kpi_state = calculate_opportunity_score(request.POST)

        # ✅ Save Suitability enable/disable settings inside kpi_state
        suit_cfg = {}
        suit_cfg["is_24_month_history"] = (
            request.POST.get("is_24_month_history_enabled", "Yes") == "Yes"
        )
        suit_cfg["has_more_than_2_sales_nominals"] = (
            request.POST.get("has_more_than_2_sales_nominals_enabled", "Yes") == "Yes"
        )
        suit_cfg["has_more_than_2_cos_nominals"] = (
            request.POST.get("has_more_than_2_cos_nominals_enabled", "Yes") == "Yes"
        )
        suit_cfg["has_more_than_10_overhead_nominals"] = (
            request.POST.get("has_more_than_10_overhead_nominals_enabled", "Yes")
            == "Yes"
        )
        suit_cfg["has_more_than_20_customers"] = (
            request.POST.get("has_more_than_20_customers_enabled", "Yes") == "Yes"
        )
        suit_cfg["has_more_than_20_suppliers"] = (
            request.POST.get("has_more_than_20_suppliers_enabled", "Yes") == "Yes"
        )
        suit_cfg["consistent_cost_base"] = (
            request.POST.get("consistent_cost_base_enabled", "Yes") == "Yes"
        )
        suit_cfg["debtor_days_calculated"] = (
            request.POST.get("debtor_days_calculated_enabled", "Yes") == "Yes"
        )
        suit_cfg["creditor_days_calculated"] = (
            request.POST.get("creditor_days_calculated_enabled", "Yes") == "Yes"
        )
        suit_cfg["stock_days_calculated"] = (
            request.POST.get("stock_days_calculated_enabled", "Yes") == "Yes"
        )
        suit_cfg["cash_balance_visible"] = (
            request.POST.get("cash_balance_visible_enabled", "Yes") == "Yes"
        )

        kpi_state = kpi_state or {}
        kpi_state["suitability_cfg"] = suit_cfg

        # IHT

        iht_cfg = {}
        iht_cfg["enabled"] = request.POST.get("iht_enabled", "Yes") == "Yes"

        try:
            iht_cfg["threshold"] = int(request.POST.get("iht_threshold", "900000"))
        except (TypeError, ValueError):
            iht_cfg["threshold"] = 900000

        kpi_state["iht_cfg"] = iht_cfg

        # Readiness

        readiness_cfg = {}
        readiness_cfg["is_ebitda_positive"] = (
            request.POST.get("readiness_is_ebitda_positive_enabled", "Yes") == "Yes"
        )
        readiness_cfg["is_ebitda_more_than_ly"] = (
            request.POST.get("readiness_is_ebitda_more_than_ly_enabled", "Yes") == "Yes"
        )

        readiness_cfg["has_dividend_last_12m"] = (
            request.POST.get("readiness_has_dividend_last_12m_enabled", "Yes") == "Yes"
        )
        readiness_cfg["is_dividend_at_least_equal_ly"] = (
            request.POST.get("readiness_is_dividend_at_least_equal_ly_enabled", "Yes")
            == "Yes"
        )

        readiness_cfg["is_cash_balance_positive"] = (
            request.POST.get("readiness_is_cash_balance_positive_enabled", "Yes")
            == "Yes"
        )
        readiness_cfg["is_cash_more_than_ly"] = (
            request.POST.get("readiness_is_cash_more_than_ly_enabled", "Yes") == "Yes"
        )

        readiness_cfg["are_sales_improving"] = (
            request.POST.get("readiness_are_sales_improving_enabled", "Yes") == "Yes"
        )

        kpi_state["readiness_cfg"] = readiness_cfg

        # ---------------- Targets for Discussion ----------------
        def _to_int_0_100(v, default):
            try:
                x = int(v)
            except (TypeError, ValueError):
                x = default
            return max(0, min(100, x))

        targets = kpi_state.get("targets") or {}

        if "target_suitability" in request.POST:
            targets["suitability"] = _to_int_0_100(
                request.POST.get("target_suitability"), 50
            )

        if "target_opportunity" in request.POST:
            targets["opportunity"] = _to_int_0_100(
                request.POST.get("target_opportunity"), 50
            )

        if "target_readiness" in request.POST:
            targets["readiness"] = _to_int_0_100(
                request.POST.get("target_readiness"), 50
            )

        def _round10(x):
            return int(round(x / 10.0) * 10)

        for k in ("suitability", "opportunity", "readiness"):
            if k in targets and targets[k] is not None:
                targets[k] = max(0, min(100, _round10(targets[k])))

        kpi_state["targets"] = targets

        criteria.kpi_state = kpi_state
        criteria.opportunity_score = opportunity_score
        criteria.save()

        return redirect("client_summary", client_id=client_id)
    # //End Post////////////////////////////////////

    # ///Start Get ///////////////////////////////////////
    # Utilities (Yes / No)
    utilities_flag = _get_client_utilities(client_id)
    # R&D
    rd_flag = _get_client_rd(client_id)
    # KPI
    kpi = _get_client_kpi(client_id)
    if kpi is None:
        raise Http404("Client KPI not found")

    # SUITABILITY
    suitability = _get_client_suitability(client_id)
    suitability_top_rows = []
    suitability_bottom_rows = []
    suitability_score = None

    # ---------------- Suitability configuration rows (for Configuration modal) ----------------
    def _is_yes(v):
        return str(v).strip().lower() == "yes"

    saved_state = criteria.kpi_state or {}
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

    if suitability:

        def yn(field):
            val = suitability.get(field)
            return str(val).strip().lower() == "yes"

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

    # IHT Start
    saved_state = criteria.kpi_state or {}
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
    # IHT End

    # READINESS
    readiness = _get_client_readiness(client_id)
    readiness_top_rows = []
    readiness_bottom_rows = []
    readiness_score = None

    saved_state = criteria.kpi_state or {}
    saved_read_cfg = saved_state.get("readiness_cfg", {}) or {}

    if readiness:

        def yn_r(field):
            val = readiness.get(field)
            return str(val).lower() == "yes"

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

    # ---------------- Readiness configuration groups Tab (for Configuration modal) ----------------
    # saved_state = criteria.kpi_state or {}
    # saved_read_cfg = saved_state.get("readiness_cfg", {}) or {}

    def _is_yes(v):
        return str(v).strip().lower() == "yes"

    readiness_config_groups = []
    if readiness:
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
                "enabled": saved_read_cfg.get("dividend", True),
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
                "enabled": saved_read_cfg.get("cash", True),
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
                "enabled": saved_read_cfg.get("sales", True),
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
                    }
                ],
            },
        ]
        readiness_config_rows = []
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

        # ----------------  Target for Discussion ----------------
    saved_state = criteria.kpi_state or {}
    targets = (saved_state.get("targets") or {}).copy()

    opportunity_score = criteria.opportunity_score

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

    # KPI TABLES (Opportunity / Working Capital)
    left_rows = []

    # Revenue vs Last Year
    rev_var = None
    if kpi["revenue_TY"] is not None and kpi["revenue_LY"] is not None:
        rev_var = kpi["revenue_TY"] - kpi["revenue_LY"]

    left_rows.append(
        {
            "label": "Revenue vs Last Year",
            "ty": kpi["revenue_TY"],
            "ly": kpi["revenue_LY"],
            "var": rev_var,
            "is_percentage": False,
        }
    )

    # Gross Margin % vs Last Year
    left_rows.append(
        {
            "label": "Gross Margin % vs Last Year",
            "ty": kpi["gross_margin_pct_TY"],
            "ly": kpi["gross_margin_pct_LY"],
            "var": kpi["gross_margin_vs_LY_pct"],
            "is_percentage": True,
        }
    )

    # Overhead £ vs Last Year
    ovh_var = None
    if kpi["overheads_TY"] is not None and kpi["overheads_LY"] is not None:
        ovh_var = kpi["overheads_TY"] - kpi["overheads_LY"]

    left_rows.append(
        {
            "label": "Overhead £ vs Last Year",
            "ty": kpi["overheads_TY"],
            "ly": kpi["overheads_LY"],
            "var": ovh_var,
            "is_percentage": False,
        }
    )

    # Overhead % vs Last Year
    left_rows.append(
        {
            "label": "Overhead % vs Last Year",
            "ty": kpi["overheads_vs_LY_pct"],
            "ly": None,
            "var": kpi["overheads_vs_LY_pct"],
            "is_percentage": True,
        }
    )

    # EBITDA vs Last Year
    left_rows.append(
        {
            "label": "EBITDA vs Last Year",
            "ty": kpi["ebitda_TY"],
            "ly": kpi["ebitda_LY"],
            "var": kpi["ebitda_vs_LY_value"],
            "is_percentage": False,
        }
    )

    # EBITDA % vs Last Year
    left_rows.append(
        {
            "label": "EBITDA % vs Last Year",
            "ty": kpi["ebitda_pct_TY"],
            "ly": kpi["ebitda_pct_LY"],
            "var": kpi["ebitda_pct_vs_LY"],
            "is_percentage": True,
        }
    )

    right_rows = []

    right_rows.append(
        {
            "label": "Cash Position (vs Last Year)",
            "ty": kpi["cash_position_TY"],
            "ly": kpi["cash_position_LY"],
            "var": kpi["cash_position_vs_LY"],
            "is_percentage": False,
        }
    )

    right_rows.append(
        {
            "label": "Debtor Days (vs Last Year)",
            "ty": kpi["debtor_days_TY"],
            "ly": kpi["debtor_days_LY"],
            "var": kpi["debtor_days_vs_LY"],
            "is_percentage": False,
        }
    )

    right_rows.append(
        {
            "label": "Creditor Days (vs Last Year)",
            "ty": kpi["creditor_days_TY"],
            "ly": kpi["creditor_days_LY"],
            "var": kpi["creditor_days_vs_LY"],
            "is_percentage": False,
        }
    )

    stock_var = None
    right_rows.append(
        {
            "label": "Stock Days (vs Last Year)",
            "ty": kpi["stock_days_TY"],
            "ly": kpi["stock_days_LY"],
            "var": stock_var,
            "is_percentage": False,
        }
    )

    div_var = None
    if kpi["dividend_TY"] is not None and kpi["dividend_LY"] is not None:
        div_var = kpi["dividend_TY"] - kpi["dividend_LY"]

    right_rows.append(
        {
            "label": "Dividend (TY / LY)",
            "ty": kpi["dividend_TY"],
            "ly": kpi["dividend_LY"],
            "var": div_var,
            "is_percentage": False,
        }
    )

    for row in left_rows:
        row["var_class"] = _var_class(row.get("var"))

    for row in right_rows:
        row["var_class"] = _var_class(row.get("var"))

    # Sales trend for chart
    sales_trend = _get_sales_trend(client_id) or []

    # OpportunityCriteria
    kpi_state = criteria.kpi_state or {}
    opportunity_score = criteria.opportunity_score

    context = {
        "client_name": kpi["client_name"],
        "client_id": kpi["client_id"],
        "left_rows": left_rows,
        "right_rows": right_rows,
        "opportunity_score": opportunity_score,
        # suitability
        "suitability_top_rows": suitability_top_rows,
        "suitability_bottom_rows": suitability_bottom_rows,
        "suitability_score": suitability_score,
        # readiness
        "readiness_top_rows": readiness_top_rows,
        "readiness_bottom_rows": readiness_bottom_rows,
        "readiness_score": readiness_score,
        # sales chart
        "sales_trend": sales_trend,
        # برای Opportunity Criteria در template
        "kpi_state": kpi_state,
        "suitability_config_rows": suitability_config_rows,
        # IHT
        "iht_enabled": iht_enabled,
        "iht_threshold": iht_threshold,
        "iht_multiple": iht_multiple,
        "iht_ebitda_ty": ebitda_ty,
        "iht_est_value": est_value,
        "iht_flag": iht_flag,
        # Readiness Tab
        "readiness_config_rows": readiness_config_rows,
        "readiness_config_groups": readiness_config_groups,
        # Utilities
        "utilities_flag": utilities_flag,
        # R&D
        "rd_flag": rd_flag,
        # Target for Discussion
        "target_suitability": target_suitability,
        "target_opportunity": target_opportunity,
        "target_readiness": target_readiness,
        "target_for_discussion": target_for_discussion,
    }
    print("SALES TREND:", sales_trend)

    return render(request, "vfd_pro/client_summary.html", context)


# ----------Call Sps for profitability ----------


# ---Revenue----
def _call_revenue_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_revenue_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, period={period}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_revenue_profitability",
                [
                    client_id,
                    period,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA.")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT => {result}")

            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_revenue_criteria(request, client_id: int):

    try:
        # ---- این‌ها مستقیم از فرم می‌آیند (اگر نباشند → KeyError) ----
        rev_enabled = request.POST["rev_enabled"]  # 'Yes' / 'No'
        # rev_period_str = request.POST["rev_period"]        # "3" / "6" / "12"
        rev_period_str = request.POST.get("rev_period", "12")
        rev_dir = request.POST["rev_dir"]  # '+/-', '+', '-'
        rev_threshold_str = request.POST["rev_threshold"]  # مثل "15.00"
        val_adj = int(request.POST.get("val_adj", 3))

        try:
            val_adj = int(request.POST.get("val_adj", 3))
        except (TypeError, ValueError):
            val_adj = 3

        try:
            rev_period = int(rev_period_str)
        except ValueError:
            return JsonResponse(
                {"ok": False, "error": "Invalid rev_period"}, status=400
            )

        try:
            rev_threshold = Decimal(rev_threshold_str)
        except Exception:
            return JsonResponse(
                {"ok": False, "error": "Invalid rev_threshold"}, status=400
            )

        rev_min_months = None

        result = _call_revenue_profitability_sp(
            client_id=client_id,
            period=rev_period,
            sign_mode=rev_dir,
            min_months=rev_min_months,
            threshold=rev_threshold,
            flag_on=rev_enabled,
        )

        if not result:
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

        return JsonResponse(data)

    except KeyError as e:

        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"},
            status=400,
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ----Start Gross Margin---


def _call_gm_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_gross_margin_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, period={period}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_gross_margin_profitability",
                [
                    client_id,
                    period,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA.")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT => {result}")

            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling GM SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_gm_criteria(request, client_id: int):

    try:
        gm_enabled = request.POST["gm_enabled"]  # 'Yes' / 'No'
        # gm_period_str = request.POST["gm_period"]        # "3" / "6" / "12"
        gm_period_str = request.POST.get("gm_period", "12")
        gm_dir = request.POST["gm_dir"]  # '+', '-', '+/-'
        gm_threshold_str = request.POST["gm_threshold"]  #  "10.00"

        val_adj = int(request.POST.get("val_adj", 3))

        try:
            val_adj = int(request.POST.get("val_adj", 3))
        except (TypeError, ValueError):
            val_adj = 3

        try:
            gm_period = int(gm_period_str)
        except ValueError:
            return JsonResponse({"ok": False, "error": "Invalid gm_period"}, status=400)

        try:
            gm_threshold = Decimal(gm_threshold_str)
        except Exception:
            return JsonResponse(
                {"ok": False, "error": "Invalid gm_threshold"}, status=400
            )

        gm_min_months = None

        result = _call_gm_profitability_sp(
            client_id=client_id,
            period=gm_period,
            sign_mode=gm_dir,
            min_months=gm_min_months,
            threshold=gm_threshold,
            flag_on=gm_enabled,
        )

        if not result:
            return JsonResponse({"ok": False, "error": "No result from SP"}, status=200)

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

        return JsonResponse(data)

    except KeyError as e:
        return JsonResponse(
            {"ok": False, "error": f"Missing field: {str(e)}"}, status=400
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# --- Start Overhead -----


def _call_overhead_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_overhead_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, period={period}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_overhead_profitability",
                [
                    client_id,
                    period,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA.")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT => {result}")

            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Overhead SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_oh_val_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_oh_val_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        oh_enabled = request.POST["oh_val_enabled"]  # 'Yes' / 'No'
        # oh_period_str = request.POST["oh_val_period"]        # "3" / "6" / "12"
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


# ---- Strart Overhead pct----
def _call_overhead_pct_profitability_sp(
    client_id, period, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_overhead_pct_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, period={period}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_overhead_pct_profitability",
                [
                    client_id,
                    period,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (Overhead %).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT => {result}")

            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Overhead PCT SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_oh_pct_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_oh_pct_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        oh_enabled = request.POST["oh_pct_enabled"]  # 'Yes' / 'No'
        # oh_period_str = request.POST["oh_pct_period"]        # "3" / "6" / "12"
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
            # "oh_pct_profit_impact": _fmt_num(result.get("Overhead_pct_Profit_Impact"), 0) if "Overhead_pct_Profit_Impact" in result else None,
            # "oh_pct_val_impact":    _fmt_num(result.get("Overhead_pct_Val_Impact"), 0)    if "Overhead_pct_Val_Impact" in result else None,
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


# -------Start Ebitda-------
def _call_ebitda_profitability_sp(client_id, sign_mode, min_months, threshold, flag_on):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_ebitda_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_ebitda_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (EBITDA).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT => {result}")

            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling EBITDA SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_ebitda_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_ebitda_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        e_enabled = request.POST["ebitda_enabled"]  # 'Yes' / 'No'
        # e_period_str = request.POST.get("ebitda_period", "12")  # "3" / "6" / "12" )
        e_period_str = request.POST.get("ebitda_period", "12")
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
            # "ebitda_impact":      _fmt_num(result.get("EBITDA_Profit_Impact"), 0) if "EBITDA_Profit_Impact" in result else None,
            # "ebitda_val_impact":  _fmt_num(result.get("EBITDA_Val_Impact"), 0)    if "EBITDA_Val_Impact" in result else None,
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


# -------Start New Customer-------
def _call_newcust_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_new_customers_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_new_customers_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )
            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW (NewCust) => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (NewCust).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS (NewCust) => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT (NewCust) => {result}")
            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling New Customers SP: {e}", exc_info=True)
        raise


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


# ---- Start Customer Retention -----


def _call_retention_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_retention_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_retention_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )
            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW (Retention) => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (Retention).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS (Retention) => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT (Retention) => {result}")
            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Retention SP: {e}", exc_info=True)
        raise


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


# --- Cash Position--


def _call_cash_position_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_cash_position_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_cash_position_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,  # None → NULL
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW (Cash) => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (Cash).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS (Cash) => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT (Cash) => {result}")
            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Cash Position SP: {e}", exc_info=True)
        raise


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
        # period_str = request.POST.get("cash_period", "var")
        direction = request.POST["cash_dir"]
        threshold_str = request.POST["cash_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => cash_enabled={enabled}, "
            # f"cash_period={period_str}, cash_dir={direction}, "
            f"cash_threshold={threshold_str}"
        )

        # try:
        #     _ = int(period_str) if period_str != "var" else None
        # except ValueError:
        #     sp_logger.warning(f"Invalid cash_period (ignored in SP): {period_str}")

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


# -- Deptor Days---


def _call_debtor_days_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_debtor_days_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_debtor_days_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW (Debtor) => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (Debtor).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS (Debtor) => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT (Debtor) => {result}")
            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Debtor Days SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_debtordays_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_debtordays_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["debtordays_enabled"]
        # period_str = request.POST.get("debtordays_period", "var")
        direction = request.POST["debtordays_dir"]
        threshold_str = request.POST["debtordays_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => debtordays_enabled={enabled}, "
            # f"debtordays_period={period_str}, debtordays_dir={direction}, "
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


# --- creditor_days --


def _call_creditor_days_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_creditor_days_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_creditor_days_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW (Creditor) => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (Creditor).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS (Creditor) => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT (Creditor) => {result}")
            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Creditor Days SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_creditordays_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_creditordays_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["creditordays_enabled"]
        # period_str = request.POST.get("creditordays_period", "var")
        direction = request.POST["creditordays_dir"]
        threshold_str = request.POST["creditordays_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => creditordays_enabled={enabled}, "
            # f"creditordays_period={period_str}, creditordays_dir={direction}, "
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


# --- Stock Days---


def _call_stock_days_profitability_sp(
    client_id, sign_mode, min_months, threshold, flag_on
):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("Calling SP: sp_vfd_client_stock_days_profitability")
    sp_logger.debug(
        f"INPUTS => client_id={client_id}, sign_mode={sign_mode}, "
        f"min_months={min_months}, threshold={threshold}, flag_on={flag_on}"
    )

    try:
        with connection.cursor() as cursor:
            cursor.callproc(
                "sp_vfd_client_stock_days_profitability",
                [
                    client_id,
                    sign_mode,
                    min_months,
                    threshold,
                    flag_on,
                ],
            )

            row = cursor.fetchone()
            sp_logger.debug(f"RAW OUTPUT ROW (Stock) => {row}")

            if row is None:
                sp_logger.debug("SP returned NO DATA (Stock).")
                return None

            columns = [col[0] for col in cursor.description]
            sp_logger.debug(f"OUTPUT COLUMNS (Stock) => {columns}")

            result = dict(zip(columns, row))
            sp_logger.debug(f"MAPPED OUTPUT (Stock) => {result}")
            return result

    except Exception as e:
        sp_logger.error(f"ERROR calling Stock Days SP: {e}", exc_info=True)
        raise


@require_POST
def ajax_stockdays_criteria(request, client_id: int):

    sp_logger.debug("--------------------------------------------------")
    sp_logger.debug("ajax_stockdays_criteria CALLED")
    sp_logger.debug(f"client_id={client_id}")
    sp_logger.debug(f"RAW POST DATA => {request.POST}")

    try:
        enabled = request.POST["stockdays_enabled"]
        # period_str = request.POST.get("stockdays_period", "var")
        direction = request.POST["stockdays_dir"]
        threshold_str = request.POST["stockdays_threshold"]

        sp_logger.debug(
            f"FORM FIELDS => stockdays_enabled={enabled}, "
            # f"stockdays_period={period_str}, stockdays_dir={direction}, "
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


def calculate_opportunity_score(post_data):

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
    flagged_count = 0
    kpi_state = {}

    for key, enabled_field, flag_field in kpis:
        enabled_val = post_data.get(enabled_field, "No")
        flag_val = post_data.get(flag_field, "No")

        enabled = enabled_val == "Yes"
        flag = flag_val == "Yes"

        kpi_state[key] = {
            "enabled": enabled,
            "flag": flag,
        }

        if enabled:
            enabled_count += 1
            if flag:
                flagged_count += 1

    if enabled_count > 0:
        score = (flagged_count / enabled_count) * 100
    else:
        score = 0

    score = round(score, 1)

    return score, kpi_state
