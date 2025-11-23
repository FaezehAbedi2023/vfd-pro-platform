from datetime import date

from django.db.models import Q
from django.shortcuts import render

from .models import ClientTransaction


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
