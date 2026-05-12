"""Майстер «Розумний підбір велосипеда» — кроки без виклику LLM."""

from __future__ import annotations

import re
from typing import Any

from django.http import HttpRequest

from velos.chat.services.recommendations import recommend_bikes

CANCEL_RE = re.compile(
    r'\b(скасув|відмін|стоп|зупин|вийти|досить|не\s*треба)\w*',
    re.IGNORECASE,
)


def _norm(s: str) -> str:
    return (s or '').strip().lower()


def extract_budget(text: str) -> int | None:
    """Витягує орієнтовний верхній бюджет у грн."""
    raw = text.replace('\u00a0', ' ')
    compact = re.sub(r'(\d)\s+(\d)', r'\1\2', raw)
    for ch in '–—':
        compact = compact.replace(ch, '-')
    # діапазон 15000-30000
    m = re.search(r'(\d{3,})\s*-\s*(\d{3,})', compact.replace(' ', ''))
    if m:
        return max(int(m.group(1)), int(m.group(2)))
    # "до 25000"
    m = re.search(r'до\s*(\d[\d\s]*)', _norm(raw))
    if m:
        digits = re.sub(r'\D', '', m.group(1))
        if len(digits) >= 3:
            return int(digits)
    # найбільше число з 3+ цифр
    nums = re.findall(r'\d{3,}', compact.replace(' ', ''))
    if nums:
        return int(max(nums, key=int))
    return None


def extract_height_band(text: str) -> str | None:
    """
    Повертає ключ: short | medium | tall | None
    """
    low = _norm(text)
    if any(x in low for x in ('160', '165', '170', 'до 175', '175-', 'низьк')):
        return 'short'
    if any(x in low for x in ('175', '180', '185', 'серед')):
        return 'medium'
    if any(x in low for x in ('185', '190', 'висок', '195', '200')):
        return 'tall'
    m = re.search(r'(\d{2,3})\s*см', low)
    if m:
        h = int(m.group(1))
        if h < 172:
            return 'short'
        if h < 183:
            return 'medium'
        return 'tall'
    return None


def map_style(text: str) -> str | None:
    low = _norm(text)
    mapping = [
        (('міст', 'комут', 'urban', 'city'), 'city'),
        (('шосе', 'road', 'швидкіс'), 'road'),
        (('граві', 'gravel', 'ліс', 'off-road'), 'gravel'),
        (('дит', 'kids'), 'kids'),
        (('електро', 'e-bike', 'ebike'), 'electric'),
        (('mtb', 'гірськ', 'trail'), 'mtb'),
    ]
    for keys, val in mapping:
        if any(k in low for k in keys):
            return val
    return None


def default_wizard_state() -> dict[str, Any]:
    return {'mode': 'none', 'bike_step': None, 'data': {}}


START_MARKERS = (
    'розумний підбір',
    'підібрати велосипед',
    'підбір велосипеда',
    'почати підбір',
    'мастер підбору',
)


def should_start_bike_wizard(message: str) -> bool:
    low = _norm(message)
    return any(m in low for m in START_MARKERS)


def handle_bike_wizard(
    request: HttpRequest,
    state: dict[str, Any],
    user_message: str,
) -> dict[str, Any] | None:
    """
    Якщо активний режим bike — повертає відповідь JSON.
    Інакше None (передати в LLM).
    """
    mode = (state or {}).get('mode') or 'none'
    if mode != 'bike':
        return None

    if CANCEL_RE.search(user_message):
        return {
            'response': 'Майстер підбору зупинено. Можете написати нове питання або знову натиснути «Розумний підбір велосипеда».',
            'quick_chips': default_chips_after_cancel(),
            'recommended_products': [],
            'wizard_state': default_wizard_state(),
        }

    low_msg = _norm(user_message)
    if low_msg in ('інший бюджет', 'змінити бюджет', 'змінити суму'):
        return {
            'response': 'Добре, вкажіть новий орієнтовний бюджет у гривнях або оберіть варіант.',
            'quick_chips': [
                'До 15 000 грн',
                '15 000 – 30 000 грн',
                '30 000 – 50 000 грн',
                'Понад 50 000 грн',
            ],
            'recommended_products': [],
            'wizard_state': {'mode': 'bike', 'bike_step': 'budget', 'data': {}},
        }

    step = state.get('bike_step') or 'budget'
    data = dict(state.get('data') or {})

    # Prefill from user profile (if available) so we don't ask again.
    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        prof = getattr(request.user, 'profile', None)
        h = getattr(prof, 'height_cm', None) if prof is not None else None
        if h and data.get('height_band') is None:
            try:
                h_int = int(h)
            except Exception:
                h_int = None
            if h_int:
                if h_int < 172:
                    data['height_band'] = 'short'
                elif h_int < 183:
                    data['height_band'] = 'medium'
                else:
                    data['height_band'] = 'tall'

    # Відновлення кроку після перезавантаження / розсинхрону клієнта
    if step == 'budget' and data.get('budget_max') is not None:
        step = 'height'
    if step == 'height' and data.get('height_band') is not None:
        step = 'style'

    # Перший крок: лише привітання + питання про бюджет
    if step == 'budget' and data.get('budget_max') is None:
        # якщо це лише тригер без числа — питаємо бюджет
        bud = extract_budget(user_message)
        triggers_only = should_start_bike_wizard(user_message) and bud is None
        if triggers_only or (not bud and len(_norm(user_message)) < 3):
            return {
                'response': (
                    'Чудово, підберемо велосипед крок за кроком.\n\n'
                    'Крок 1 з 3. Який у вас орієнтовний бюджет (у гривнях)? '
                    'Можна написати суму або обрати варіант вище.'
                ),
                'quick_chips': [
                    'До 15 000 грн',
                    '15 000 – 30 000 грн',
                    '30 000 – 50 000 грн',
                    'Понад 50 000 грн',
                ],
                'recommended_products': [],
                'wizard_state': {'mode': 'bike', 'bike_step': 'budget', 'data': data},
            }
        if bud is None:
            return {
                'response': 'Не зміг розпізнати суму. Напишіть бюджет числом (наприклад 25000) або оберіть кнопку вище.',
                'quick_chips': [
                    'До 15 000 грн',
                    '15 000 – 30 000 грн',
                    '30 000 – 50 000 грн',
                    'Понад 50 000 грн',
                ],
                'recommended_products': [],
                'wizard_state': {'mode': 'bike', 'bike_step': 'budget', 'data': data},
            }
        data['budget_max'] = bud
        if data.get('height_band') is not None:
            return {
                'response': (
                    f'Дякую! Бюджет до {bud:,} грн зафіксовано.\n\n'
                    'Бачу ваш зріст у профілі — пропускаю цей крок.\n\n'
                    'Крок 3 з 3. Де плануєте катати найчастіше? '
                    'Це допоможе обрати тип велосипеда.'
                ),
                'quick_chips': [
                    'Місто / комʼютер',
                    'Шосе',
                    'Гравій / ліс',
                    'Гірський / MTB',
                    'Електровелосипед',
                ],
                'recommended_products': [],
                'wizard_state': {'mode': 'bike', 'bike_step': 'style', 'data': data},
            }
        return {
            'response': (
                f'Дякую! Бюджет до {bud:,} грн зафіксовано.\n\n'
                'Крок 2 з 3. Вкажіть приблизний зріст (для орієнтиру по розміру рами) — '
                'числом у см або оберіть діапазон.'
            ),
            'quick_chips': ['160 – 172 см', '172 – 182 см', '182 см і вище'],
            'recommended_products': [],
            'wizard_state': {'mode': 'bike', 'bike_step': 'height', 'data': data},
        }

    if step == 'height' and data.get('height_band') is None:
        band = extract_height_band(user_message)
        if band is None:
            return {
                'response': 'Оберіть зріст кнопкою або напишіть, наприклад: 175 см.',
                'quick_chips': ['160 – 172 см', '172 – 182 см', '182 см і вище'],
                'recommended_products': [],
                'wizard_state': {'mode': 'bike', 'bike_step': 'height', 'data': data},
            }
        data['height_band'] = band
        return {
            'response': (
                'Чудово, записав.\n\n'
                'Крок 3 з 3. Де плануєте катати найчастіше? '
                'Це допоможе обрати тип велосипеда.'
            ),
            'quick_chips': [
                'Місто / комʼютер',
                'Шосе',
                'Гравій / ліс',
                'Гірський / MTB',
                'Електровелосипед',
            ],
            'recommended_products': [],
            'wizard_state': {'mode': 'bike', 'bike_step': 'style', 'data': data},
        }

    if step == 'style' and data.get('style') is None:
        style = map_style(user_message)
        if style is None:
            return {
                'response': 'Оберіть стиль катання кнопкою вище або опишіть своїми словами (місто, шосе, гравій…).',
                'quick_chips': [
                    'Місто / комʼютер',
                    'Шосе',
                    'Гравій / ліс',
                    'Гірський / MTB',
                    'Електровелосипед',
                ],
                'recommended_products': [],
                'wizard_state': {'mode': 'bike', 'bike_step': 'style', 'data': data},
            }
        data['style'] = style
        budget_max = data.get('budget_max')
        products = recommend_bikes(request, budget_max, style, limit=6)
        lines = [
            'Ось варіанти з нашого каталогу, які підходять під ваш запит:',
            '',
        ]
        if not products:
            lines.append(
                'За цими критеріями зараз мало позицій у каталозі. '
                f'Перегляньте всі велосипеди: {request.build_absolute_uri("/catalog/")}'
            )
        else:
            for i, p in enumerate(products, 1):
                lines.append(f'{i}. [{p["name"]}]({p["url"]}) — {p["price"]} грн')
        return {
            'response': '\n'.join(lines),
            'quick_chips': [
                'Інший бюджет',
                'Підібрати екіпірування',
                'Порадити трасу',
                'До каталогу',
            ],
            'recommended_products': products,
            'wizard_state': default_wizard_state(),
        }

    # Несподіваний стан — скидаємо
    return {
        'response': 'Почнімо спочатку: натисніть «Розумний підбір велосипеда».',
        'quick_chips': default_chips_after_cancel(),
        'recommended_products': [],
        'wizard_state': default_wizard_state(),
    }


def default_chips_after_cancel() -> list[str]:
    return [
        'Розумний підбір велосипеда',
        'Екіпірування для початківця',
        'Траси поруч',
        'Відкрити каталог',
    ]
