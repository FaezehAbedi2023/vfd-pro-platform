from decimal import Decimal, ROUND_HALF_UP


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
