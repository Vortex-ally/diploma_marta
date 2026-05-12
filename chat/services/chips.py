"""Динамічні швидкі підказки після відповіді (евристики)."""

from __future__ import annotations


def suggest_chips(user_message: str, assistant_message: str) -> list[str]:
    u = (user_message or '').lower()
    a = (assistant_message or '').lower()
    combined = f'{u} {a}'

    chips: list[str] = []

    if any(
        w in combined
        for w in (
            'велосипед',
            'байк',
            'рама',
            'колес',
            'шосе',
            'граві',
            'mtb',
            'електро',
        )
    ):
        chips.extend(['Розумний підбір велосипеда', 'Для міста чи траси?', 'До 25 000 грн — що є?'])

    if any(w in combined for w in ('екіпі', 'шолом', 'рукавич', 'окуляр', 'взутт', 'ліхтар')):
        chips.extend(['Шоломи', 'Велоодяг', 'Що взяти початківцю?'])

    if any(w in combined for w in ('трас', 'маршрут', 'покатат', 'куди поїхати')):
        chips.extend(['Траси у Львові', 'Легкі траси для початківців', 'Відкрити всі траси'])

    if any(w in combined for w in ('магазин', 'купити офлайн', 'адрес')):
        chips.append('Де магазини VeloUkraine?')

    # Унікальні, порядок збережено
    seen: set[str] = set()
    out: list[str] = []
    for c in chips:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out[:6]
