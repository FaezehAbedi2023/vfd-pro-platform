from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime


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


def _var_class(value):
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


def _round10_or_none(v):
    if v is None:
        return None

    if not isinstance(v, Decimal):
        v = Decimal(str(v))

    ten = Decimal("10")

    return int((v / ten).to_integral_value(rounding=ROUND_HALF_UP) * ten)


def format_month_year(value) -> str:
    """
    Converts:
      - 'YYYY-MM'  -> 'Feb 2025'

    """
    if value is None:
        return "-"

    if isinstance(value, (date, datetime)):
        return value.strftime("%b %Y")  # Feb 2025

    s = str(value).strip()

    # exact YYYY-MM
    if len(s) == 7 and s[4] == "-":
        try:
            y = int(s[:4])
            m = int(s[5:7])
            dt = date(y, m, 1)
            return dt.strftime("%b %Y")
        except Exception:
            return s

    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%b %Y")
    except Exception:
        return s
