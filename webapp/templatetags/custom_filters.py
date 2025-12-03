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


@register.simple_tag(takes_context=True)
def category_label(context, category):
    """
    Возвращает отображаемое название категории.
    Для языка 'en' используется slug с заглавной буквы, иначе оригинальное имя.
    """
    try:
        lang = context.get('LANGUAGE_CODE') or context.get('request').LANGUAGE_CODE
    except Exception:
        lang = context.get('LANGUAGE_CODE', 'ru')

    if lang == 'en':
        # slug -> Title Case (только первая буква заглавная для простых слагов)
        s = (getattr(category, 'slug', '') or '').replace('-', ' ')
        return s.title()
    return getattr(category, 'name', '')
