"""Контекст каталогу та трас для промпта."""

from urllib.parse import quote

from velos.bikes.models import Product, Trail

from velos.chat.constants import CATALOG_RULES


def site_knowledge_block(request) -> str:
    """Компактний зріз каталогу для контексту моделі."""
    base = request.build_absolute_uri('/').rstrip('/')
    lines = [CATALOG_RULES.format(base=base), '', f'БАЗОВИЙ URL: {base}', '']

    # User context for better recommendations (only for authenticated users)
    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        prof = getattr(request.user, 'profile', None)
        if prof is not None:
            u = []
            if getattr(prof, 'gender', None) and prof.gender not in ('', 'na'):
                try:
                    u.append(f"стать: {prof.get_gender_display()}")
                except Exception:
                    u.append(f"стать: {prof.gender}")
            if getattr(prof, 'age', None):
                u.append(f"вік: {prof.age}")
            if getattr(prof, 'height_cm', None):
                u.append(f"ріст: {prof.height_cm} см")
            if getattr(prof, 'weight_kg', None):
                u.append(f"вага: {prof.weight_kg} кг")
            if getattr(prof, 'city', None):
                city = (prof.city or '').strip()
                if city:
                    u.append(f"місто: {city}")
            if u:
                lines.append('——— ПАРАМЕТРИ КОРИСТУВАЧА (для підбору) ———')
                lines.append('• ' + ' | '.join(u))
                lines.append('')

    lines.append('——— ВЕЛОСИПЕДИ ТА ЕКІПІРУВАННЯ (товари сайту) ———')
    qs = (
        Product.objects.select_related('category', 'brand')
        .order_by('category__category_type', '-is_featured', 'name')[:350]
    )
    for p in qs:
        kind = 'велосипед' if p.category.category_type == 'bike' else 'екіпірування'
        brand = p.brand.name if p.brand else '—'
        price = int(p.price)
        short = (p.short_description or '')[:100] or (p.description or '')[:100]
        short = short.replace('\n', ' ').strip()
        url = request.build_absolute_uri(f'/product/{p.slug}/')
        extra = []
        if p.wheel_size:
            extra.append(f'колесо {p.wheel_size}"')
        if p.range_km:
            extra.append(f'запас ходу ~{p.range_km} км')
        if p.frame_size:
            extra.append(f'рама {p.frame_size}')
        spec = '; '.join(extra) if extra else ''
        line = (
            f'• {p.name} | {kind} | категорія: {p.category.name} | {price} грн | {brand}'
            f'{" | " + spec if spec else ""} | URL: {url}'
        )
        if short:
            line += f' | Коротко: {short}'
        lines.append(line)

    lines.append('')
    lines.append('——— ТРАСИ (є на сайті) ———')
    for t in Trail.objects.all().order_by('city', 'name')[:100]:
        diff = t.get_difficulty_display()
        ttype = t.get_trail_type_display()
        trail_url = request.build_absolute_uri(f'/trails/?city={quote(t.city)}')
        desc = (t.description or '')[:150].replace('\n', ' ')
        lines.append(
            f'• {t.name} | {t.city} | {t.distance_km} км | {diff} | тип: {ttype} | '
            f'~{t.duration_hours} год | посилання за містом: {trail_url}'
            + (f' | Опис: {desc}' if desc else '')
        )

    lines.append('')
    lines.append(f'Загальна сторінка трас: {request.build_absolute_uri("/trails/")}')
    lines.append(f'Магазини (офлайн точки): {request.build_absolute_uri("/stores/")}')
    return '\n'.join(lines)
