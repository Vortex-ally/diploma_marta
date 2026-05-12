from __future__ import annotations

from dataclasses import dataclass

from velos.bikes.models import Product


SESSION_KEY = 'velo_cart_v1'


@dataclass(frozen=True)
class CartLine:
    product: Product
    qty: int


def _get_raw_cart(session) -> dict:
    raw = session.get(SESSION_KEY)
    if isinstance(raw, dict):
        return raw
    return {}


def cart_count(session) -> int:
    raw = _get_raw_cart(session)
    total = 0
    for k, v in raw.items():
        try:
            total += int(v.get('qty', 0) or 0)
        except Exception:
            continue
    return max(0, total)


def cart_lines(session) -> list[CartLine]:
    raw = _get_raw_cart(session)
    ids: list[int] = []
    qty_map: dict[int, int] = {}
    for k, v in raw.items():
        try:
            pid = int(k)
            qty = int(v.get('qty', 0) or 0)
        except Exception:
            continue
        if qty > 0:
            ids.append(pid)
            qty_map[pid] = qty

    products = (
        Product.objects.filter(pk__in=ids)
        .select_related('brand', 'category')
        .prefetch_related('images')
    )
    by_id = {p.id: p for p in products}
    out: list[CartLine] = []
    for pid in ids:
        p = by_id.get(pid)
        if p:
            out.append(CartLine(product=p, qty=qty_map.get(pid, 1)))
    return out


def cart_total(session) -> float:
    total = 0.0
    for line in cart_lines(session):
        total += float(line.product.price) * int(line.qty)
    return total


def add_to_cart(session, product_id: int, qty: int = 1) -> None:
    qty = int(qty or 0)
    if qty <= 0:
        return
    raw = _get_raw_cart(session)
    key = str(int(product_id))
    cur = raw.get(key) or {}
    cur_qty = int(cur.get('qty', 0) or 0)
    raw[key] = {'qty': max(1, cur_qty + qty)}
    session[SESSION_KEY] = raw
    session.modified = True


def set_qty(session, product_id: int, qty: int) -> None:
    qty = int(qty or 0)
    raw = _get_raw_cart(session)
    key = str(int(product_id))
    if qty <= 0:
        raw.pop(key, None)
    else:
        raw[key] = {'qty': qty}
    session[SESSION_KEY] = raw
    session.modified = True


def remove_from_cart(session, product_id: int) -> None:
    raw = _get_raw_cart(session)
    raw.pop(str(int(product_id)), None)
    session[SESSION_KEY] = raw
    session.modified = True

