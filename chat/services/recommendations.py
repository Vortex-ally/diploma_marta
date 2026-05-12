"""Підбір товарів з БД для майстра велосипеда."""

from django.http import HttpRequest

from velos.bikes.models import Product


STYLE_TO_BIKE_TYPES = {
    'city': ['road', 'electric', 'gravel'],
    'road': ['road'],
    'gravel': ['gravel'],
    'kids': ['kids'],
    'electric': ['electric'],
    'mtb': ['gravel', 'electric'],
}


def recommend_bikes(
    request: HttpRequest,
    budget_max: int | None,
    style_key: str | None,
    limit: int = 6,
) -> list[dict]:
    """
    Повертає список словників для JSON-відповіді фронту.
    """
    qs = (
        Product.objects.select_related('category', 'brand')
        .filter(category__category_type='bike', in_stock=True)
    )
    if budget_max and budget_max > 0:
        qs = qs.filter(price__lte=budget_max)

    types = STYLE_TO_BIKE_TYPES.get((style_key or 'city').lower(), STYLE_TO_BIKE_TYPES['city'])
    qs = qs.filter(category__bike_type__in=types)

    qs = qs.order_by('-is_featured', '-rating', 'price')[:limit]

    out = []
    for p in qs:
        img = p.image_src
        if img and not img.startswith('http'):
            img = request.build_absolute_uri(img)
        out.append(
            {
                'id': p.id,
                'name': p.name,
                'url': request.build_absolute_uri(f'/product/{p.slug}/'),
                'price': int(p.price),
                'brand': p.brand.name if p.brand else '',
                'image': img or '',
                'bike_type': (
                    p.category.get_bike_type_display()
                    if getattr(p.category, 'bike_type', None)
                    else ''
                ),
            }
        )
    return out
