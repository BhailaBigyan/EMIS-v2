from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Return mapping[key] or None. Useful for dict lookups in templates."""
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def multiply(value, factor):
    try:
        return value * factor
    except (TypeError, ValueError):
        return 0


@register.filter
def divide(value, divisor):
    try:
        if divisor == 0:
            return 0
        return value / divisor
    except (TypeError, ValueError):
        return 0