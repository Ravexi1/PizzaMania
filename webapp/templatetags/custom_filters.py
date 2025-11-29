from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Умножить value на arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def format_price(value):
    """Форматирование цены без лишних нулей"""
    try:
        price = float(value)
        if price == int(price):
            return str(int(price))
        return f"{price:.1f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return value
