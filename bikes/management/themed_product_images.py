"""
Тематичні фото для демо-товарів (Unsplash, стабільні посилання).
Підбираються за категорією, щоб зображення відповідало типу товару.
"""
import zlib

# Параметри зображення (якість і ширина для каталогу)
_Q = 'ixlib=rb-4.0.3&auto=format&fit=crop&w=1400&q=82'
_B = 'https://images.unsplash.com'


def _u(photo_path: str) -> str:
    return f'{_B}/{photo_path}?{_Q}'


# Пули: кілька варіантів на категорію — різні товари отримують різні фото (стабільно від ключа)
_IMAGE_POOLS = {
    # Велосипеди
    'road': [
        _u('photo-1541625602330-2277a4c46182'),
        _u('photo-1544191696-102dbdaeeaa0'),
        _u('photo-1532298229144-0ec0c57515c7'),
        _u('photo-1576435728678-68d0fbf94e91'),
        _u('photo-1485965120184-e220f721d03e'),
        _u('photo-1506905925346-21bda4d32df4'),
    ],
    'gravel': [
        _u('photo-1441974231531-c6227db76b6e'),
        _u('photo-1464822759023-fed622ff2c3b'),
        _u('photo-1500530855697-b586d89ba3ee'),
        _u('photo-1519331379826-f10be5486c6f'),
        _u('photo-1571068316344-75bc76f77890'),
        _u('photo-1507525428034-b723cf961d3e'),
    ],
    'kids': [
        _u('photo-1485965120184-e220f721d03e'),
        _u('photo-1576435728678-68d0fbf94e91'),
        _u('photo-1544191696-102dbdaeeaa0'),
        _u('photo-1541625602330-2277a4c46182'),
        _u('photo-1532298229144-0ec0c57515c7'),
    ],
    'electric': [
        _u('photo-1576435728678-68d0fbf94e91'),
        _u('photo-1558618666-fcd25c85cd64'),
        _u('photo-1541625602330-2277a4c46182'),
        _u('photo-1532298229144-0ec0c57515c7'),
        _u('photo-1506905925346-21bda4d32df4'),
    ],
    # Екіпірування
    'helmet': [
        _u('photo-1601925260368-ae2f83cf8b7f'),
        _u('photo-1566576912321-d58ddd7a6088'),
        _u('photo-1556909114-f6e7ad7d3136'),
        _u('photo-1571019613454-1cb2f99b2d8b'),
        _u('photo-1511994298241-608e28f14fde'),
        _u('photo-1601925260368-ae2f83cf8b7f'),  # intentional repeat for short pools
    ],
    'clothing': [
        _u('photo-1511994298241-608e28f14fde'),
        _u('photo-1571019613454-1cb2f99b2d8b'),
        _u('photo-1558618666-fcd25c85cd64'),
        _u('photo-1523381210434-271e8be1f52b'),
        _u('photo-1542291026-7eec264c27ff'),
        _u('photo-1596462502278-27bfdc403348'),
    ],
    'glasses': [
        _u('photo-1583394838336-acd977736f90'),
        _u('photo-1596462502278-27bfdc403348'),
        _u('photo-1511707171634-5f897ff02aa9'),
        _u('photo-1571019613454-1cb2f99b2d8b'),
        _u('photo-1523381210434-271e8be1f52b'),
    ],
    'shoes': [
        _u('photo-1542291026-7eec264c27ff'),
        _u('photo-1523381210434-271e8be1f52b'),
        _u('photo-1601925260368-ae2f83cf8b7f'),
        _u('photo-1511994298241-608e28f14fde'),
        _u('photo-1596462502278-27bfdc403348'),
    ],
    'gloves': [
        _u('photo-1504274066651-8d31a536b11a'),
        _u('photo-1452860606245-08befc0ff44b'),
        _u('photo-1571019613454-1cb2f99b2d8b'),
        _u('photo-1583394838336-acd977736f90'),
        _u('photo-1556909114-f6e7ad7d3136'),
    ],
    'lights': [
        _u('photo-1553062407-98eeb64c6a62'),
        _u('photo-1589939705384-5185137a7f0f'),
        _u('photo-1452860606245-08befc0ff44b'),
        _u('photo-1511707171634-5f897ff02aa9'),
        _u('photo-1504148455328-c376907d081c'),
    ],
    'locks': [
        _u('photo-1589829545856-d10d557cf95f'),
        _u('photo-1586864387967-d02ef85d93e8'),
        _u('photo-1452860606245-08befc0ff44b'),
        _u('photo-1504148455328-c376907d081c'),
        _u('photo-1553062407-98eeb64c6a62'),
    ],
    'bags': [
        _u('photo-1553062407-98eeb64c6a62'),
        _u('photo-1589939705384-5185137a7f0f'),
        _u('photo-1452860606245-08befc0ff44b'),
        _u('photo-1566576912321-d58ddd7a6088'),
        _u('photo-1511994298241-608e28f14fde'),
    ],
    'tools': [
        _u('photo-1504148455328-c376907d081c'),
        _u('photo-1452860606245-08befc0ff44b'),
        _u('photo-1589829545856-d10d557cf95f'),
        _u('photo-1586864387967-d02ef85d93e8'),
        _u('photo-1553062407-98eeb64c6a62'),
    ],
    'accessories': [
        _u('photo-1485965120184-e220f721d03e'),
        _u('photo-1511707171634-5f897ff02aa9'),
        _u('photo-1576435728678-68d0fbf94e91'),
        _u('photo-1541625602330-2277a4c46182'),
        _u('photo-1589939705384-5185137a7f0f'),
    ],
    'default': [
        _u('photo-1541625602330-2277a4c46182'),
        _u('photo-1485965120184-e220f721d03e'),
        _u('photo-1576435728678-68d0fbf94e91'),
    ],
}


def pick_themed_image(category_slug: str, unique_key: str) -> str:
    """
    Повертає URL зображення для категорії (slug Category: road, helmet, lights, …).
    unique_key — назва товару або seed для стабільного вибору з пулу.
    """
    pool = _IMAGE_POOLS.get(category_slug) or _IMAGE_POOLS['default']
    if not pool:
        pool = _IMAGE_POOLS['default']
    h = zlib.adler32(unique_key.encode('utf-8'))
    return pool[h % len(pool)]


def pick_bike_image(bike_type_slug: str, product_name: str) -> str:
    """Для велосипедів за bike_type (road, gravel, kids, electric)."""
    return pick_themed_image(bike_type_slug, product_name)
