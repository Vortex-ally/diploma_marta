from django import template

register = template.Library()


@register.filter(name="split_csv")
def split_csv(value: str):
    """
    Split comma-separated sizes into a list.
    Example: "38, 39,40" -> ["38","39","40"]
    """
    if not value:
        return []
    return [p.strip() for p in str(value).split(",") if p.strip()]

