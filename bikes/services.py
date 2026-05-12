"""Допоміжна логіка каталогу та рекомендацій (без дублювання в views)."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from django.db.models import Q, Count

from bikes.models import Product, Trail, RidePost, RideRequest, UserSubscription

_TRAIL_TYPES_FOR_BIKE = {
    'road': ('road', 'mixed'),
    'gravel': ('mixed', 'mtb', 'road'),
    'electric': ('city', 'mixed', 'road'),
    'kids': ('city',),
}

_BIKE_TYPES_FOR_TRAIL = {
    'road': ('road', 'gravel'),
    'mtb': ('gravel', 'electric', 'road'),
    'city': ('electric', 'road', 'kids'),
    'mixed': ('gravel', 'road', 'electric'),
}


def get_product_suggestions(product: Product, limit: int = 8) -> list[Product]:
    """
    Спочатку товари з тієї ж категорії та/або з подібними тегами,
    потім інші з того ж типу (bike/gear).
    """
    tag_names = list(product.tags.values_list('name', flat=True)[:25]) if getattr(product, 'tags', None) else []
    if tag_names:
        tagged = list(
            Product.objects.filter(tags__name__in=tag_names)
            .exclude(pk=product.pk)
            .select_related('brand', 'category')
            .annotate(_tag_hits=Count('tags'))
            .order_by('-_tag_hits', '-is_featured', '-rating', '-created_at')
            .distinct()[:limit]
        )
        if len(tagged) >= limit:
            return tagged[:limit]
    else:
        tagged = []

    same_cat = list(
        Product.objects.filter(category=product.category)
        .exclude(pk=product.pk)
        .select_related('brand', 'category')
        .order_by('-is_featured', '-rating', '-created_at')[:limit]
    )
    # merge tagged + same_cat without duplicates
    out = []
    seen = {product.pk}
    for p in tagged + same_cat:
        if p.pk in seen:
            continue
        out.append(p)
        seen.add(p.pk)
        if len(out) >= limit:
            return out[:limit]

    ids = {product.pk, *(p.pk for p in out)}
    remaining = limit - len(out)
    extra = list(
        Product.objects.filter(category__category_type=product.category.category_type)
        .exclude(pk__in=ids)
        .select_related('brand', 'category')
        .order_by('-is_featured', '-rating', '-created_at')[:remaining]
    )
    return out + extra


def recompute_product_rating(product: Product) -> None:
    """
    Перерахунок Байєсівського середнього рейтингу та кількості відгуків.
    """
    reviews = product.reviews.all()
    cnt = reviews.count()
    if cnt == 0:
        product.rating = 0.0
        product.reviews_count = 0
    else:
        # Звичайна зважена сума для товару
        total_weight = 0.0
        weighted_sum = 0.0
        for r in reviews:
            weight = 1.5 if getattr(r, 'is_verified', False) else 1.0
            weighted_sum += int(r.rating) * weight
            total_weight += weight
            
        R = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Bayesian Formula: (v / (v + m)) * R + (m / (v + m)) * C
        C = 4.0  # Глобальний середній рейтинг
        m = 3.0  # Поріг довіри (мін. к-сть відгуків для впливу)
        v = float(cnt)
        
        bayesian_rating = (v / (v + m)) * R + (m / (v + m)) * C
        product.rating = round(bayesian_rating, 2)
        product.reviews_count = cnt
        
    product.save(update_fields=['rating', 'reviews_count'])


def get_suggested_trails_for_bike(product: Product, limit: int = 4) -> tuple[list[Trail], str | None]:
    """
    Траси, які найкраще пасують під тип велосипеда.
    Повертає (список траси, перший тип траси для фільтра на /trails/?type=).
    Для не-велосипедів — порожній список.
    """
    if product.category.category_type != 'bike':
        return [], None
    bt = product.category.bike_type
    order = _TRAIL_TYPES_FOR_BIKE.get(bt, ('mixed', 'road'))
    q = Q(trail_type__in=order)
    if bt == 'kids':
        q &= Q(difficulty='easy')

    trails = list(
        Trail.objects.filter(q)
        .order_by('-rating', '-distance_km')[: max(limit * 3, 12)]
    )
    rank = {t: i for i, t in enumerate(order)}
    trails.sort(key=lambda tr: (rank.get(tr.trail_type, 99), -float(tr.rating or 0)))
    primary_filter = order[0] if order else None
    out = trails[:limit]
    if not out:
        out = list(Trail.objects.order_by('-rating', '-distance_km')[:limit])
    return out, primary_filter


def get_suggested_bikes_for_trail(trail: Trail, limit: int = 6) -> list[Product]:
    """
    Велосипеди з каталогу, на яких доречно їхати цей маршрут.
    """
    order = _BIKE_TYPES_FOR_TRAIL.get(trail.trail_type, ('gravel', 'road', 'electric'))
    rank = {t: i for i, t in enumerate(order)}

    qs = (
        Product.objects.filter(
            category__category_type='bike',
            category__bike_type__in=list(order),
            in_stock=True,
        )
        .select_related('brand', 'category')
        .order_by('-is_featured', '-rating', '-created_at')
    )
    if trail.difficulty in ('hard', 'extreme'):
        qs = qs.exclude(category__bike_type='kids')

    bikes = list(qs[: max(limit * 4, 24)])
    bikes.sort(key=lambda p: (rank.get(p.category.bike_type, 99), -float(p.rating or 0)))
    out = bikes[:limit]
    if not out:
        out = list(
            Product.objects.filter(category__category_type='bike', in_stock=True)
            .select_related('brand', 'category')
            .order_by('-is_featured', '-rating')[:limit]
        )
    return out


def get_or_create_subscription(user) -> UserSubscription | None:
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    sub = UserSubscription.objects.filter(user=user).first()
    if sub:
        return sub
    sub = UserSubscription.objects.create(user=user, tier='free', status='active')
    return sub


def is_premium(user) -> bool:
    sub = get_or_create_subscription(user)
    if not sub:
        return False
    return sub.tier == 'premium' and sub.status == 'active'


def can_create_post(user) -> tuple[bool, str]:
    """
    Free: max 1 active post.
    Premium: unlimited.
    """
    if is_premium(user):
        return True, ''
    active = RidePost.objects.filter(author=user, is_active=True).count()
    if active >= 1:
        return False, 'Для Free доступний 1 активний пост. Підключіть Premium, щоб створювати більше.'
    return True, ''


def can_send_request(user) -> tuple[bool, str]:
    """
    Free: max 3 requests per day.
    Premium: unlimited.
    """
    if is_premium(user):
        return True, ''
    today = timezone.now().date()
    used = RideRequest.objects.filter(requester=user, created_at__date=today).count()
    if used >= 3:
        return False, 'Для Free доступно 3 заявки на день. Підключіть Premium, щоб надсилати більше.'
    return True, ''
