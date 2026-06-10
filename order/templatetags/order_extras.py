from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Умножение двух чисел"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
