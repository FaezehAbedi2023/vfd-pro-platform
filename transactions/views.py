from datetime import date
from django.db.models import Q
from django.shortcuts import render
from .models import ClientTransaction
from django.http import HttpResponse
from io import BytesIO
import openpyxl
import os
from .vfd_collect_report_data import get_metrics_from_database, get_derived_metrics
from django.db import connection
from django.http import Http404
from django.shortcuts import render
import json


def portfolio_view(request):
    qs = ClientTransaction.objects.all()

    # فیلترها از query string
    search = request.GET.get('search', '').strip()

    selected_sources = request.GET.getlist('source')
    selected_categories = request.GET.getlist('category')
    selected_currencies = request.GET.getlist('currency_code')

    year = request.GET.get('year', '')
    month = request.GET.get('month', '')

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

    transactions = qs.order_by('-transaction_date', '-id')[:10]

    available_sources = (
        ClientTransaction.objects
        .exclude(source__isnull=True)
        .exclude(source__exact='')
        .values_list('source', flat=True)
        .distinct()
        .order_by('source')
    )

    available_categories = (
        ClientTransaction.objects
        .exclude(category__isnull=True)
        .exclude(category__exact='')
        .values_list('category', flat=True)
        .distinct()
        .order_by('category')
    )

    available_currencies = (
        ClientTransaction.objects
        .exclude(currency_code__isnull=True)
        .exclude(currency_code__exact='')
        .values_list('currency_code', flat=True)
        .distinct()
        .order_by('currency_code')
    )

    current_year = date.today().year
    years = list(range(current_year - 5, current_year + 1))

    months = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
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

    return render(request, "transactions/portfolio.html", context)


def download_vfd_report(request):
    # config از همون environment هایی میاد که تو docker-compose تعریف کردی
    config = {
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "host": os.environ.get("DB_HOST"),
        "port": int(os.environ.get("DB_PORT")),   # "3306" -> 3306
        "database": os.environ.get("DB_NAME"),
    }

    # فعلاً برای تست:
    client_id = 9312   # بعداً می‌تونی از URL یا فرم بگیری

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
            "SELECT * FROM vfd_client_kpis WHERE client_id = %s",
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
                creditor_days_calculated,
                stock_days_calculated,
                cash_balance_visible,
                consistent_cost_base,
                CNT_inconsistent_months_12
            FROM vfd_client_suitability
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
    داده‌های Readiness از vfd_client_Readiness
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                client_id,
                client_name,
                is_ebitda_positive,
                val_ebitda_TY,
                is_ebitda_more_than_ly,
                val_ebitda_vs_ly,
                has_dividend_last_12m,
                val_dividend_TY,
                is_dividend_at_least_equal_ly,
                val_dividend_vs_ly,
                is_cash_balance_positive,
                val_cash_TY,
                is_cash_more_than_ly,
                val_cash_vs_ly,
                are_sales_improving,
                val_revenue_vs_ly
            FROM vfd_client_Readiness
            WHERE client_id = %s
            """,
            [client_id],
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))


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


# ---------- View اصلی ----------

def client_summary(request, client_id: int):
    # KPI اصلی
    kpi = _get_client_kpi(client_id)
    if kpi is None:
        raise Http404("Client KPI not found")

    # SUITABILITY
    suitability = _get_client_suitability(client_id)
    suitability_top_rows = []
    suitability_bottom_rows = []
    suitability_score = None

    if suitability:
        def yn(field):
            val = suitability.get(field)
            return str(val).lower() == "yes"

        suitability_top_rows = [
            {"label": "24 Months History", "value": yn("is_24_month_history")},
            {
                "label": "More Than 2 Sales Nominals",
                "value": yn("has_more_than_2_sales_nominals"),
            },
            {
                "label": "More Than 2 COS Nominals",
                "value": yn("has_more_than_2_cos_nominals"),
            },
            {
                "label": "More Than 10 Overhead Nominals",
                "value": yn("has_more_than_10_overhead_nominals"),
            },
            {
                "label": "More Than 20 Customers",
                "value": yn("has_more_than_20_customers"),
            },
            {
                "label": "More Than 20 Suppliers",
                "value": yn("has_more_than_20_suppliers"),
            },
        ]

        suitability_bottom_rows = [
            {"label": "Consistent Cost Base", "value": yn("consistent_cost_base")},
            {"label": "Debtor Days Calculated", "value": yn("debtor_days_calculated")},
            {
                "label": "Creditor Days Calculated",
                "value": yn("creditor_days_calculated"),
            },
            {"label": "Stock Days Calculated", "value": yn("stock_days_calculated")},
            {"label": "Cash Balance Visible", "value": yn("cash_balance_visible")},
        ]

        all_flags = suitability_top_rows + suitability_bottom_rows
        yes_count = sum(1 for r in all_flags if r["value"])
        total_count = len(all_flags)
        suitability_score = round(100 * yes_count / total_count) if total_count else None

    # READINESS
    readiness = _get_client_readiness(client_id)
    readiness_top_rows = []
    readiness_bottom_rows = []
    readiness_score = None

    if readiness:
        def yn_r(field):
            val = readiness.get(field)
            return str(val).lower() == "yes"

        readiness_top_rows = [
            {
                "label": "Is The Client's EBITDA Positive?",
                "value": yn_r("is_ebitda_positive"),
            },
            {
                "label": "Is The EBITDA More Than Last Year?",
                "value": yn_r("is_ebitda_more_than_ly"),
            },
            {
                "label": "Have They Paid A Dividend In The Last 12 Months?",
                "value": yn_r("has_dividend_last_12m"),
            },
            {
                "label": "Is The Dividend At Least Equal To Last Year?",
                "value": yn_r("is_dividend_at_least_equal_ly"),
            },
        ]

        readiness_bottom_rows = [
            {
                "label": "Is The Cash Balance Positive?",
                "value": yn_r("is_cash_balance_positive"),
            },
            {
                "label": "Is The Cash Balance More Than Last Year?",
                "value": yn_r("is_cash_more_than_ly"),
            },
            {
                "label": "Are Sales Improving?",
                "value": yn_r("are_sales_improving"),
            },
        ]

        all_r_flags = readiness_top_rows + readiness_bottom_rows
        yes_r = sum(1 for r in all_r_flags if r["value"])
        total_r = len(all_r_flags)
        readiness_score = round(100 * yes_r / total_r) if total_r else None

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
    # sales_trend = _get_sales_trend(client_id)
    sales_trend = _get_sales_trend(client_id) or []

 
    # فعلاً Opportunity Score رو 0 می‌ذاریم
    opportunity_score = 0

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
       
    }
    print("SALES TREND:", sales_trend)

    return render(request, "transactions/client_summary.html", context)
