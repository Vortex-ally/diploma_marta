"""
Management command to populate sample data for VeloUkraine
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from bikes.models import Category, Brand, Product, Store, StoreLocation, ProductStore, Trail
from bikes.management.themed_product_images import pick_themed_image


class Command(BaseCommand):
    help = 'Populate database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚲 Створення категорій...')
        self.create_categories()
        self.stdout.write('🏷️ Створення брендів...')
        self.create_brands()
        self.stdout.write('🚲 Створення велосипедів...')
        self.create_bikes()
        self.stdout.write('🎒 Створення екіпірування...')
        self.create_gear()
        self.stdout.write('🖼️ Оновлення фото для всіх товарів...')
        self.ensure_all_images()
        self.stdout.write('🏪 Створення магазинів...')
        self.create_stores()
        self.stdout.write('📍 Створення точок магазинів...')
        self.create_store_locations()
        self.stdout.write('🗺️ Створення трас...')
        self.create_trails()
        self.stdout.write(self.style.SUCCESS('✅ Дані успішно додано!'))

    def upsert_product(self, *, name, defaults):
        """
        Create product if it doesn't exist, otherwise update missing/changed fields.
        This keeps demo DB consistent after design/content updates.
        """
        obj, created = Product.objects.get_or_create(name=name, defaults=defaults)
        if created:
            self.stdout.write(f'  ✓ {name}')
            return obj

        changed = False
        for k, v in defaults.items():
            if k == 'name':
                continue
            if v is None:
                continue
            current = getattr(obj, k, None)
            # Поля сумок завжди синхронізуємо з сіду (повний блок «особливості / обсяг…»).
            if k.startswith('bag_') and v not in (None, ''):
                if current != v:
                    setattr(obj, k, v)
                    changed = True
            elif current in (None, '', 0) and v not in (None, ''):
                setattr(obj, k, v)
                changed = True
            elif k == 'image_url' and v and current != v:
                setattr(obj, k, v)
                changed = True

        if changed:
            obj.save()
            self.stdout.write(f'  ↻ {name}')
        return obj

    def themed_photo(self, category_slug: str, product_name: str) -> str:
        """Тематичне фото Unsplash за типом категорії та назвою товару."""
        return pick_themed_image(category_slug, product_name)

    def ensure_all_images(self):
        from bikes.models import ProductImage
        updated = 0
        qs = Product.objects.select_related('category').prefetch_related('images').all()
        for p in qs:
            if p.image and p.image.url.startswith('http'):
                continue
            url = (p.image_url or '').strip()
            needs_update = (
                not url
                or 'picsum' in url
                or url.startswith('/media/')
            )
            if needs_update:
                slug = p.category.slug if p.category_id else 'default'
                new_url = pick_themed_image(slug, p.name)
                p.image_url = new_url
                p.save(update_fields=['image_url'])
                updated += 1
            else:
                new_url = url

            # Sync primary ProductImage so product detail gallery works
            first = p.images.order_by('sort_order', 'id').first()
            if first and not first.image:
                old = (first.image_url or '').strip()
                if not old or old.startswith('/media/') or 'picsum' in old:
                    first.image_url = new_url
                    first.save(update_fields=['image_url'])
            elif not p.images.exists() and new_url:
                ProductImage.objects.create(
                    product=p, image_url=new_url, alt=p.name, sort_order=0
                )
        self.stdout.write(f'  ↻ фото додано/оновлено: {updated}')

    def create_categories(self):
        cats = [
            # Bikes
            {'name': 'Шосейні велосипеди', 'slug': 'road', 'category_type': 'bike', 'bike_type': 'road', 'icon': '🚵'},
            {'name': 'Гравійні велосипеди', 'slug': 'gravel', 'category_type': 'bike', 'bike_type': 'gravel', 'icon': '🪨'},
            {'name': 'Дитячі велосипеди', 'slug': 'kids', 'category_type': 'bike', 'bike_type': 'kids', 'icon': '👦'},
            {'name': 'Електровелосипеди', 'slug': 'electric', 'category_type': 'bike', 'bike_type': 'electric', 'icon': '⚡'},
            # Gear
            {'name': 'Шоломи', 'slug': 'helmet', 'category_type': 'gear', 'gear_type': 'helmet', 'icon': '⛑️'},
            {'name': 'Вело-форма', 'slug': 'clothing', 'category_type': 'gear', 'gear_type': 'clothing', 'icon': '👕'},
            {'name': 'Окуляри', 'slug': 'glasses', 'category_type': 'gear', 'gear_type': 'glasses', 'icon': '🕶️'},
            {'name': 'Вело-туфлі', 'slug': 'shoes', 'category_type': 'gear', 'gear_type': 'shoes', 'icon': '👟'},
            {'name': 'Рукавички', 'slug': 'gloves', 'category_type': 'gear', 'gear_type': 'gloves', 'icon': '🧤'},
            {'name': 'Ліхтарі', 'slug': 'lights', 'category_type': 'gear', 'gear_type': 'lights', 'icon': '💡'},
            {'name': 'Замки', 'slug': 'locks', 'category_type': 'gear', 'gear_type': 'locks', 'icon': '🔐'},
            {'name': 'Сумки', 'slug': 'bags', 'category_type': 'gear', 'gear_type': 'bags', 'icon': '🎒'},
            {'name': 'Інструменти', 'slug': 'tools', 'category_type': 'gear', 'gear_type': 'tools', 'icon': '🔧'},
            {'name': 'Аксесуари', 'slug': 'accessories', 'category_type': 'gear', 'gear_type': 'accessories', 'icon': '⚙️'},
        ]
        for c in cats:
            Category.objects.get_or_create(slug=c['slug'], defaults=c)

    def create_brands(self):
        brands = [
            {'name': 'Trek', 'slug': 'trek', 'country': 'США'},
            {'name': 'Giant', 'slug': 'giant', 'country': 'Тайвань'},
            {'name': 'Specialized', 'slug': 'specialized', 'country': 'США'},
            {'name': 'Scott', 'slug': 'scott', 'country': 'Швейцарія'},
            {'name': 'Merida', 'slug': 'merida', 'country': 'Тайвань'},
            {'name': 'Cannondale', 'slug': 'cannondale', 'country': 'США'},
            {'name': 'Cube', 'slug': 'cube', 'country': 'Німеччина'},
            {'name': 'Haibike', 'slug': 'haibike', 'country': 'Німеччина'},
            {'name': 'Author', 'slug': 'author', 'country': 'Тайвань'},
            {'name': 'Formula', 'slug': 'formula', 'country': 'Тайвань'},
            {'name': 'Canyon', 'slug': 'canyon', 'country': 'Німеччина'},
            {'name': 'Rose', 'slug': 'rose', 'country': 'Німеччина'},
            {'name': 'Factor', 'slug': 'factor', 'country': 'Велика Британія'},
            {'name': 'Twitter', 'slug': 'twitter', 'country': 'Китай'},
            {'name': 'Temple', 'slug': 'temple', 'country': 'Велика Британія'},
            {'name': 'Fuji', 'slug': 'fuji', 'country': 'Японія'},
            {'name': 'Belsize', 'slug': 'belsize', 'country': 'Велика Британія'},
            {'name': 'Youthkkee', 'slug': 'youthkkee', 'country': 'Китай'},
            {'name': 'Rocker', 'slug': 'rocker', 'country': 'США'},
            {'name': 'Cubsala', 'slug': 'cubsala', 'country': 'Китай'},
            {'name': 'Fatboy', 'slug': 'fatboy', 'country': 'Нідерланди'},
            {'name': 'Verde', 'slug': 'verde', 'country': 'США'},
            {'name': 'Colony', 'slug': 'colony', 'country': 'Австралія'},
            {'name': 'Leitner', 'slug': 'leitner', 'country': 'Австралія'},
            {'name': 'Leichten', 'slug': 'leichten', 'country': 'Німеччина'},
            {'name': 'Alwaybike', 'slug': 'alwaybike', 'country': 'Китай'},
            {'name': 'Lekker', 'slug': 'lekker', 'country': 'Нідерланди'},
        ]
        for b in brands:
            Brand.objects.get_or_create(slug=b['slug'], defaults=b)

    def create_bikes(self):
        road_cat = Category.objects.get(slug='road')
        gravel_cat = Category.objects.get(slug='gravel')
        kids = Category.objects.get(slug='kids')
        electric = Category.objects.get(slug='electric')
        trek = Brand.objects.get(slug='trek')
        giant = Brand.objects.get(slug='giant')
        specialized = Brand.objects.get(slug='specialized')
        merida = Brand.objects.get(slug='merida')
        cube = Brand.objects.get(slug='cube')
        haibike = Brand.objects.get(slug='haibike')
        author = Brand.objects.get(slug='author')
        scott = Brand.objects.get(slug='scott')
        cannondale = Brand.objects.get(slug='cannondale')
        formula = Brand.objects.get(slug='formula')
        canyon = Brand.objects.get(slug='canyon')
        rose = Brand.objects.get(slug='rose')
        factor = Brand.objects.get(slug='factor')
        twitter = Brand.objects.get(slug='twitter')
        temple = Brand.objects.get(slug='temple')
        fuji = Brand.objects.get(slug='fuji')
        belsize = Brand.objects.get(slug='belsize')
        youthkkee = Brand.objects.get(slug='youthkkee')
        rocker = Brand.objects.get(slug='rocker')
        cubsala = Brand.objects.get(slug='cubsala')
        fatboy = Brand.objects.get(slug='fatboy')
        verde = Brand.objects.get(slug='verde')
        colony = Brand.objects.get(slug='colony')
        leitner = Brand.objects.get(slug='leitner')
        leichten = Brand.objects.get(slug='leichten')
        alwaybike = Brand.objects.get(slug='alwaybike')
        lekker = Brand.objects.get(slug='lekker')

        bikes = [
            # Шосейні / гравійні (демо-асортимент)
            {
                'name': 'Trek Marlin 7 Gen 2', 'category': road_cat, 'brand': trek,
                'price': 38000, 'old_price': 42000,
                'short_description': 'Гірський велосипед для серйозного катання',
                'description': 'Trek Marlin 7 — надійний гірський велосипед з алюмінієвою рамою Alpha Gold. Оснащений 12-швидкісною трансмісією Shimano Deore та гідравлічними гальмами. Підвіска RockShox Judy Silver TK 100mm забезпечує чудове поглинання ударів.',
                'wheel_size': '29', 'speeds': 12, 'frame_material': 'Алюміній',
                'weight': 13.8, 'color': 'Синій матовий',
                'is_featured': True, 'is_new': True, 'rating': 4.8, 'reviews_count': 47,
                'in_stock': True,
            },
            {
                'name': 'Giant Trance X 29 2', 'category': road_cat, 'brand': giant,
                'price': 95000, 'old_price': None,
                'short_description': 'Повнопідвісний MTB для екстремального катання',
                'description': 'Giant Trance X 29 — повнопідвісний гірський велосипед з карбоновою рамою. Підвіска Fox 34 Float 140mm спереду та Fox Float DPS 140mm ззаду. Гальма Shimano XT, трансмісія SRAM GX Eagle 12s.',
                'wheel_size': '29', 'speeds': 12, 'frame_material': 'Карбон',
                'weight': 12.1, 'color': 'Чорний',
                'is_featured': True, 'rating': 4.9, 'reviews_count': 23,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-07.png',
            },
            {
                'name': 'Merida Big.Nine 300', 'category': road_cat, 'brand': merida,
                'price': 22500,
                'description': 'Хардтейл MTB для початківців та любителів. Алюмінієва рама, вилка Suntour XCM 100mm, трансмісія Shimano Acera 3x8.',
                'wheel_size': '29', 'speeds': 24, 'frame_material': 'Алюміній',
                'weight': 14.5, 'color': 'Сірий',
                'is_featured': True, 'rating': 4.5, 'reviews_count': 89,
                'in_stock': True,
            },
            {
                'name': 'Trek Domane AL 3', 'category': road_cat, 'brand': trek,
                'price': 52000,
                'description': 'Шосейний велосипед для ендуро-їзди. Алюмінієва рама з IsoSpeed технологією. Groupset Shimano Tiagra 2x10, гальма кантілевер.',
                'wheel_size': '700c', 'speeds': 20, 'frame_material': 'Алюміній',
                'weight': 9.8, 'color': 'Червоний',
                'is_featured': False, 'rating': 4.7, 'reviews_count': 34,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-05.png',
            },
            {
                'name': 'Specialized Rockhopper Expert', 'category': road_cat, 'brand': specialized,
                'price': 45000, 'old_price': 52000,
                'description': 'Хардтейл XC з алюмінієвою рамою FACT. Вилка RockShox Judy TK 100mm, трансмісія SRAM NX Eagle 12-швидкісна.',
                'wheel_size': '29', 'speeds': 12, 'frame_material': 'Алюміній',
                'weight': 13.2, 'color': 'Зелений',
                'is_featured': True, 'rating': 4.6, 'reviews_count': 56,
                'in_stock': True,
            },

            {
                'name': "Giant Liv Avail AR 4", 'category': gravel_cat, 'brand': giant,
                'price': 28000,
                'description': 'Жіночий шосейний велосипед з алюмінієвою рамою. Комфортна геометрія D-Fuse підсідельний штир. Shimano Sora 2x9.',
                'wheel_size': '700c', 'speeds': 18, 'frame_material': 'Алюміній',
                'weight': 9.5, 'color': 'Рожевий',
                'is_featured': True, 'rating': 4.7, 'reviews_count': 31,
                'in_stock': True,
            },
            {
                'name': "Trek FX 3 Disc Women's", 'category': gravel_cat, 'brand': trek,
                'price': 31000,
                'description': 'Жіночий міський велосипед. Алюмінієва рама, гідравлічні гальма Shimano, трансмісія 24 швидкості.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Алюміній',
                'weight': 11.2, 'color': 'Білий',
                'is_featured': True, 'rating': 4.8, 'reviews_count': 44,
                'in_stock': True,
            },
            {
                'name': 'Merida Crossway 40 Lady', 'category': gravel_cat, 'brand': merida,
                'price': 14500,
                'description': 'Жіночий комфортний велосипед для міста та легких прогулянок. Подовжена вилка для зручної посадки.',
                'wheel_size': '28', 'speeds': 21, 'frame_material': 'Алюміній',
                'weight': 13.8, 'color': 'Фіолетовий',
                'is_featured': False, 'rating': 4.4, 'reviews_count': 67,
                'in_stock': True,
            },

            # Kids
            {
                'name': 'Author Matrix 20', 'category': kids, 'brand': author,
                'price': 6800,
                'description': 'Дитячий велосипед для дітей 6-9 років. Легка алюмінієва рама, ручні гальма, додаткові колеса в комплекті.',
                'wheel_size': '20', 'speeds': 6, 'frame_material': 'Алюміній',
                'weight': 9.2, 'color': 'Синій',
                'age_min': 6, 'age_max': 9,
                'is_featured': True, 'rating': 4.6, 'reviews_count': 112,
                'in_stock': True,
            },
            {
                'name': 'Giant ARX 24', 'category': kids, 'brand': giant,
                'price': 10500,
                'description': 'Дитячий велосипед для підлітків 8-12 років. Алюмінієва рама, Shimano Altus 8-швидкісний, гідравлічні гальма.',
                'wheel_size': '24', 'speeds': 8, 'frame_material': 'Алюміній',
                'weight': 10.8, 'color': 'Жовтий',
                'age_min': 8, 'age_max': 12,
                'is_featured': True, 'rating': 4.8, 'reviews_count': 78,
                'in_stock': True,
            },
            {
                'name': 'Trek Precaliber 12', 'category': kids, 'brand': trek,
                'price': 5500,
                'description': 'Бігова каталка для малюків 2-4 роки. Без педалей, вчить балансувати. Ергономічне сідло.',
                'wheel_size': '12', 'speeds': 1, 'frame_material': 'Алюміній',
                'weight': 4.1, 'color': 'Червоний',
                'age_min': 2, 'age_max': 4,
                'is_featured': False, 'rating': 4.9, 'reviews_count': 203,
                'in_stock': True,
            },

            # Electric (фото: catalog/user-*, electric-01…07 та electric-09…16)
            {
                'name': 'Haibike SDURO HardNine 5.0', 'category': electric, 'brand': haibike,
                'price': 72000,
                'description': 'Електричний гірський велосипед з мотором Yamaha PW-SE 250W. Батарея 500Wh, запас ходу до 80 км. 10-швидкісна трансмісія Shimano Deore.',
                'wheel_size': '29', 'speeds': 10, 'frame_material': 'Алюміній',
                'weight': 22.5, 'color': 'Чорний/Помаранчевий',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт', 'range_km': 80,
                'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 28,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-03.png',
            },
            {
                'name': 'Cube Reaction Hybrid Pro 500', 'category': electric, 'brand': cube,
                'price': 85000,
                'description': 'Електро-MTB з мотором Bosch Performance CX 250W. Батарея 500Wh, інтегрована в раму. До 120 км запасу ходу.',
                'wheel_size': '29', 'speeds': 11, 'frame_material': 'Алюміній',
                'weight': 23.8, 'color': 'Сірий/Зелений',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт (75 Нм)', 'range_km': 120,
                'is_featured': True, 'rating': 4.9, 'reviews_count': 15,
                'in_stock': True,
                'image_url': '/media/products/electric/electric-02.png',
            },
            {
                'name': 'Trek Powerfly 5 Gen 4', 'category': electric, 'brand': trek,
                'price': 68000,
                'description': 'Електро-MTB для трейлів і міста. Мотор Bosch Performance Line, батарея 500 Wh, запас ходу до 100 км. Трансмісія Shimano Deore 10s.',
                'wheel_size': '29', 'speeds': 10, 'frame_material': 'Алюміній',
                'weight': 21.2, 'color': 'Синій металік',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт', 'range_km': 100,
                'is_featured': True, 'rating': 4.6, 'reviews_count': 19,
                'in_stock': True,
                'image_url': '/media/products/electric/electric-03.png',
            },
            {
                'name': 'Specialized Turbo Vado 4.0', 'category': electric, 'brand': specialized,
                'price': 92000,
                'description': 'Міський електровелосипед з мотором Specialized 2.2, батарея 710 Wh. Комфортна геометрія, передня підвіска, гальма гідравлічні.',
                'wheel_size': '700c', 'speeds': 11, 'frame_material': 'Алюміній',
                'weight': 24.1, 'color': 'Сріблястий',
                'battery_capacity': '710 Wh', 'motor_power': '250 Вт', 'range_km': 110,
                'is_featured': True, 'rating': 4.8, 'reviews_count': 22,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-09.png',
            },
            {
                'name': 'Giant Explore E+ 2 GTS', 'category': electric, 'brand': giant,
                'price': 78000,
                'description': 'Туристичний електровелосипед: мотор SyncDrive Sport, батарея EnergyPak 500 Wh, передня підвіска, багажник і крила.',
                'wheel_size': '28', 'speeds': 10, 'frame_material': 'Алюміній',
                'weight': 25.0, 'color': 'Білий/Чорний',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт', 'range_km': 95,
                'is_featured': False, 'rating': 4.5, 'reviews_count': 11,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-01.png',
            },
            {
                'name': 'Scott Axis eRide 20', 'category': electric, 'brand': scott,
                'price': 71000,
                'description': 'Електро-хардтейл з мотором Bosch Active Line Plus, батарея 500 Wh. Легка алюмінієва рама, гальма дискові.',
                'wheel_size': '29', 'speeds': 9, 'frame_material': 'Алюміній',
                'weight': 22.8, 'color': 'Сіро-блакитний',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт', 'range_km': 85,
                'is_featured': False, 'rating': 4.4, 'reviews_count': 9,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-04.png',
            },
            {
                'name': 'Cannondale Adventure Neo 3', 'category': electric, 'brand': cannondale,
                'price': 65000,
                'description': 'Комфортний електровелосипед з низькою рамою. Мотор Bosch Active Line, батарея 400 Wh, ідеально для міста та парків.',
                'wheel_size': '28', 'speeds': 9, 'frame_material': 'Алюміній',
                'weight': 23.5, 'color': 'Графіт',
                'battery_capacity': '400 Wh', 'motor_power': '250 Вт', 'range_km': 70,
                'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 14,
                'in_stock': True,
                'image_url': '/media/products/catalog/user-08.png',
            },

            # Додаткові моделі (різні типи та ціни)
            {
                'name': 'Cannondale Synapse AL 105', 'category': road_cat, 'brand': cannondale,
                'price': 48500,
                'short_description': 'Шосейник для довгих дистанцій',
                'description': 'Алюмінієва рама SmartForm, геометрія endurance. Група Shimano 105 2x11, дискові гальма. Комфортна посадка для тренувань і туру.',
                'wheel_size': '700c', 'speeds': 22, 'frame_material': 'Алюміній',
                'weight': 9.4, 'color': 'Синій',
                'is_featured': False, 'rating': 4.7, 'reviews_count': 41, 'in_stock': True,
            },
            {
                'name': 'Scott Addict 30', 'category': road_cat, 'brand': scott,
                'price': 62000, 'old_price': 68000,
                'short_description': 'Легкий шосейник з карбону',
                'description': 'Карбонова рама HMF, вилка повністю карбонова. Shimano Tiagra 2x10, покришки Schwalbe One. Для швидких групових заїздів.',
                'wheel_size': '700c', 'speeds': 20, 'frame_material': 'Карбон HMF',
                'weight': 8.2, 'color': 'Чорний/Жовтий',
                'is_featured': True, 'is_new': True, 'rating': 4.8, 'reviews_count': 27, 'in_stock': True,
                'image_url': '/media/products/catalog/user-02.png',
            },
            {
                'name': 'Merida Scultura 400', 'category': road_cat, 'brand': merida,
                'price': 39500,
                'description': 'Шосейний алюмінієвий байк з карбоновою вилкою. Shimano 105, легка рама з технологією Double Chamber.',
                'wheel_size': '700c', 'speeds': 22, 'frame_material': 'Алюміній',
                'weight': 8.9, 'color': 'Червоний металік',
                'is_featured': False, 'rating': 4.6, 'reviews_count': 52, 'in_stock': True,
            },
            {
                'name': 'Trek X-Caliber 8', 'category': road_cat, 'brand': trek,
                'price': 33500,
                'description': 'Хардтейл XC: RockShox Judy Silver, трансмісія SRAM SX Eagle 12s, колеса 29". Універсально для лісу та легкого трейлу.',
                'wheel_size': '29', 'speeds': 12, 'frame_material': 'Алюміній',
                'weight': 13.1, 'color': 'Зелений ліс',
                'is_featured': True, 'rating': 4.5, 'reviews_count': 63, 'in_stock': True,
            },

            # Шосейні (локальні фото road-01…09)
            {
                'name': 'Rose Pro SL Disc Di2', 'category': road_cat, 'brand': rose,
                'price': 112000,
                'short_description': 'Карбон endurance, Shimano 105 Di2',
                'description': 'Шосейний велосипед Rose: сіро-біла карбонова рама, гідравлічні дискові гальма, покришки Continental GP5000, інтегрована проводка. Геометрія для швидких тренувань і довгих дистанцій.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон',
                'weight': 8.1, 'color': 'Сірий мат',
                'is_featured': True, 'is_new': True, 'rating': 4.9, 'reviews_count': 12, 'in_stock': True,
                'image_url': '/media/products/road/road-01.png',
            },
            {
                'name': 'Canyon Ultimate CF SLX', 'category': road_cat, 'brand': canyon,
                'price': 198000,
                'short_description': 'Топ шосе: Ultegra Di2, DT Swiss',
                'description': 'Canyon Ultimate CF SLX — глянцевий карбон, Shimano Ultegra Di2, колеса DT Swiss з глибоким ободом, покришки Pirelli P Zero Race, інтегроване кермо. Для гонок і максимальної швидкості на асфальті.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон',
                'weight': 7.3, 'color': 'Чорний глянець',
                'is_featured': True, 'rating': 4.95, 'reviews_count': 9, 'in_stock': True,
                'image_url': '/media/products/road/road-02.png',
            },
            {
                'name': 'Scott Addict RC SRAM Red AXS', 'category': road_cat, 'brand': scott,
                'price': 245000,
                'short_description': 'Бездротовий SRAM Red eTap AXS',
                'description': 'Scott Addict RC: карбон HMX, бездротова трансмісія SRAM Red eTap AXS, гідравлічні диски, глибокі карбонові колеса Syncros, покришки Schwalbe. Іридесцентні акценти на рамі та вилці.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон HMX',
                'weight': 6.9, 'color': 'Чорний / ірис',
                'is_featured': True, 'is_new': True, 'rating': 5.0, 'reviews_count': 7, 'in_stock': True,
                'image_url': '/media/products/road/road-03.png',
            },
            {
                'name': 'Merida Reacto 7000 Disc', 'category': road_cat, 'brand': merida,
                'price': 89500,
                'short_description': 'Аеро шосе, Shimano 105, диски',
                'description': 'Аеродинамічна рама з металевим бронзовим лаком, повна група Shimano 105 2x12, гідравлічні дискові гальма, покришки Mitas. Універсальний вибір для критерію та групових заїздів.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон',
                'weight': 8.0, 'color': 'Бронза металік',
                'is_featured': False, 'rating': 4.75, 'reviews_count': 18, 'in_stock': True,
                'image_url': '/media/products/road/road-04.png',
            },
            {
                'name': 'Factor O2 VAM Ultegra Di2', 'category': road_cat, 'brand': factor,
                'price': 215000,
                'short_description': 'Легкий карбон O2 VAM, Di2',
                'description': 'Factor O2 VAM: агресивна геометрія гонки, Shimano Ultegra Di2, колеса Black Inc, покришки Goodyear Eagle F1, інтегрований карбоновий кокпіт. Голографічні написи FACTOR на рамі.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон TeXtreme',
                'weight': 6.9, 'color': 'Чорний мат / prism',
                'is_featured': True, 'rating': 4.92, 'reviews_count': 5, 'in_stock': True,
                'image_url': '/media/products/road/road-05.png',
            },
            {
                'name': 'Cannondale SuperSix EVO LAB71', 'category': road_cat, 'brand': cannondale,
                'price': 289000,
                'short_description': 'Флагман LAB71, SRAM Red AXS',
                'description': 'Cannondale LAB71 SuperSix EVO: карбон з текстурою forged carbon, SRAM Red AXS, колеса HollowGram, покришки Vittoria Corsa Pro з бежевими боками. Преміум аерошосе для перемог.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон LAB71',
                'weight': 6.8, 'color': 'Чорний / золото',
                'is_featured': True, 'is_new': True, 'rating': 5.0, 'reviews_count': 4, 'in_stock': True,
                'image_url': '/media/products/road/road-06.png',
            },
            {
                'name': 'Scott Addict RC Team Issue', 'category': road_cat, 'brand': scott,
                'price': 228000,
                'short_description': 'Командна специфікація Addict RC',
                'description': 'Scott Addict RC з повним SRAM Red eTap AXS, глибокими Syncros, дисками та покришками Schwalbe. Іридесцентні смуги на вилці та ланцюгових стійках.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон HMX-SL',
                'weight': 6.95, 'color': 'Темно-сірий ірис',
                'is_featured': False, 'rating': 4.88, 'reviews_count': 11, 'in_stock': True,
                'image_url': '/media/products/road/road-07.png',
            },
            {
                'name': 'Scott Addict RC Pro AXS', 'category': road_cat, 'brand': scott,
                'price': 235000,
                'short_description': 'Addict RC Pro, повний Red AXS',
                'description': 'Високий рівень оснащення: SRAM Red eTap AXS, інтегрований кермовий комплекс Syncros, карбонове підсідло, дискові гальма з великими роторами. Для шосейних гонок і рекордів.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон',
                'weight': 6.92, 'color': 'Матовий чорний ірис',
                'is_featured': True, 'rating': 4.9, 'reviews_count': 8, 'in_stock': True,
                'image_url': '/media/products/road/road-08.png',
            },
            {
                'name': 'Canyon Ultimate CF SL 8', 'category': road_cat, 'brand': canyon,
                'price': 165000,
                'short_description': 'Ultimate CF SL, Ultegra Di2',
                'description': 'Canyon Ultimate: чорний карбон, Shimano Ultegra Di2, колеса DT Swiss, Pirelli P Zero, сідло Selle Italia. Збалансована жорсткість і комфорт для довгих дистанцій.',
                'wheel_size': '700c', 'speeds': 24, 'frame_material': 'Карбон',
                'weight': 7.5, 'color': 'Чорний stealth',
                'is_featured': False, 'rating': 4.85, 'reviews_count': 14, 'in_stock': True,
                'image_url': '/media/products/road/road-09.png',
            },
            {
                'name': 'Cube Nuroad Pro', 'category': gravel_cat, 'brand': cube,
                'price': 42000,
                'short_description': 'Гравійник з дисками GRX',
                'description': 'Алюмінієва рама з місцем під крила та багажник. Shimano GRX 2x11, покришки 40 мм, геометрія для міксу асфальту та гравію.',
                'wheel_size': '700c', 'speeds': 22, 'frame_material': 'Алюміній',
                'weight': 10.8, 'color': 'Сірий',
                'is_featured': True, 'rating': 4.7, 'reviews_count': 35, 'in_stock': True,
            },
            {
                'name': 'Cannondale Topstone 4', 'category': gravel_cat, 'brand': cannondale,
                'price': 35800,
                'description': 'Вхідний гравійник: міцна рама, вилка карбонова, MicroSHIFT 10 швидкостей, дискові механічні гальма.',
                'wheel_size': '700c', 'speeds': 10, 'frame_material': 'Алюміній',
                'weight': 11.4, 'color': 'Оливковий',
                'is_featured': False, 'rating': 4.5, 'reviews_count': 48, 'in_stock': True,
            },
            {
                'name': 'Scott Addict Gravel 20', 'category': gravel_cat, 'brand': scott,
                'price': 89000,
                'description': 'Карбоновий гравій з інтегрованою кермовою. SRAM Rival AXS 12s, колеса Syncros. Для швидких гравійних гонок.',
                'wheel_size': '700c', 'speeds': 12, 'frame_material': 'Карбон',
                'weight': 9.1, 'color': 'Чорний мат',
                'is_featured': True, 'rating': 4.9, 'reviews_count': 19, 'in_stock': True,
            },

            # Гравійні (локальні фото gravel-01…08)
            {
                'name': 'Cube Nuroad SL GRX 1x11', 'category': gravel_cat, 'brand': cube,
                'price': 54800,
                'short_description': 'GRX 1x, Schwalbe G-One',
                'description': 'Гравійний Cube з матовою сірою рамою, трансмісія Shimano GRX 1x, гідравлічні диски, покришки Schwalbe G-One. Внутрішня проводка, дроп-бари для міксу асфальту та бездоріжжя.',
                'wheel_size': '700c', 'speeds': 11, 'frame_material': 'Алюміній',
                'weight': 10.2, 'color': 'Сірий мат',
                'is_featured': True, 'is_new': True, 'rating': 4.82, 'reviews_count': 16, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-01.png',
            },
            {
                'name': 'Twitter Gravel Carbon 1x', 'category': gravel_cat, 'brand': twitter,
                'price': 48500,
                'short_description': 'Карбон, білий лак, 1x',
                'description': 'Легка карбонова рама білого кольору, трансмісія 1x з широкою касетою, дискові гальма, широкі шипасті покришки. Для швидкого гравію та bikepacking.',
                'wheel_size': '700c', 'speeds': 11, 'frame_material': 'Карбон',
                'weight': 9.8, 'color': 'Білий глянець',
                'is_featured': False, 'rating': 4.65, 'reviews_count': 9, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-02.png',
            },
            {
                'name': 'Giant Revolt Advanced 2', 'category': gravel_cat, 'brand': giant,
                'price': 92000,
                'short_description': 'Карбон, WTB, двоколірна рама',
                'description': 'Giant Revolt: синьо-сірий карбон, геометрія adventure, 1x привід, покришки WTB з агресивним протектором, кріплення для фляг та сумок на рамі та вилці.',
                'wheel_size': '700c', 'speeds': 12, 'frame_material': 'Карбон',
                'weight': 9.4, 'color': 'Синій / темно-сірий',
                'is_featured': True, 'rating': 4.88, 'reviews_count': 22, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-03.png',
            },
            {
                'name': 'Temple Adventure GRX 600', 'category': gravel_cat, 'brand': temple,
                'price': 62000,
                'short_description': 'Сталь, tan-wall, Hunt',
                'description': 'Сталева рама Temple темно-графітова, Shimano GRX 1x, диски, ободи Hunt, покришки з бежевим боком. Класичний вигляд і надійність для далеких поїздок.',
                'wheel_size': '700c', 'speeds': 11, 'frame_material': 'Сталь CrMo',
                'weight': 11.0, 'color': 'Графіт / tan wall',
                'is_featured': False, 'rating': 4.7, 'reviews_count': 11, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-04.png',
            },
            {
                'name': 'Merida Silex 7000 GRX', 'category': gravel_cat, 'brand': merida,
                'price': 78500,
                'short_description': 'GRX 2x, флейр дропи',
                'description': 'Алюмінієва рама металік, Shimano GRX 2x, гідравлічні диски, дроп-бари з флейром, покришки Maxxis Rambler. Універсал для гравію та лісу.',
                'wheel_size': '700c', 'speeds': 22, 'frame_material': 'Алюміній',
                'weight': 10.5, 'color': 'Сріблястий металік',
                'is_featured': True, 'rating': 4.8, 'reviews_count': 19, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-05.png',
            },
            {
                'name': 'Fuji Jari 1.3 WTB Riddler', 'category': gravel_cat, 'brand': fuji,
                'price': 52000,
                'short_description': 'WTB Riddler gumwall',
                'description': 'Fuji Jari: сріблясто-сіра рама з білими акцентами, 2x трансмісія, диски, покришки WTB Riddler з класичними tan sidewalls. Кріплення для багажу та крил.',
                'wheel_size': '700c', 'speeds': 20, 'frame_material': 'Алюміній',
                'weight': 10.9, 'color': 'Срібний / білий',
                'is_featured': False, 'rating': 4.6, 'reviews_count': 14, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-06.png',
            },
            {
                'name': 'Cube Nuroad FE CUES Flatbar', 'category': gravel_cat, 'brand': cube,
                'price': 43800,
                'short_description': 'Плоске кермо, Shimano CUES',
                'description': 'Гравій/міський гібрид зі світлою рамою, привід Shimano CUES 1x, гідравлічні диски, покришки Schwalbe G-One Allround, зручне плоске кермо для міста та легкого бездоріжжя.',
                'wheel_size': '700c', 'speeds': 11, 'frame_material': 'Алюміній',
                'weight': 10.6, 'color': 'Світло-сірий',
                'is_featured': True, 'rating': 4.72, 'reviews_count': 13, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-07.png',
            },
            {
                'name': 'Canyon Grail CF SLX Force AXS', 'category': gravel_cat, 'brand': canyon,
                'price': 198000,
                'short_description': 'Топ гравій: Force eTap, DT Swiss',
                'description': 'Canyon Grail CF SLX: карбон чорний/лавандовий, SRAM Force eTap AXS 1x, колеса DT Swiss GRC 1400, покришки Pirelli Cinturato Gravel, інтегроване дроп-кермо. Максимум для швидкого гравію.',
                'wheel_size': '700c', 'speeds': 12, 'frame_material': 'Карбон',
                'weight': 8.6, 'color': 'Чорний / лаванда',
                'is_featured': True, 'is_new': True, 'rating': 4.95, 'reviews_count': 6, 'in_stock': True,
                'image_url': '/media/products/gravel/gravel-08.png',
            },
            {
                'name': 'Formula Kid 16"', 'category': kids, 'brand': formula,
                'price': 5200,
                'description': 'Дитячий 16" з додатковими колесами в комплекті. Ручні та ножні гальма, захист ланцюга, яскраві кольори.',
                'wheel_size': '16', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 8.5, 'color': 'Помаранчевий',
                'age_min': 4, 'age_max': 7,
                'is_featured': False, 'rating': 4.5, 'reviews_count': 91, 'in_stock': True,
            },
            {
                'name': 'Author Compact 26"', 'category': kids, 'brand': author,
                'price': 11800,
                'description': 'Підлітковий 26" для зростання 140–165 см. Shimano Altus 3x7, амортизаційна вилка 60 мм, надійні гальма V-brake.',
                'wheel_size': '26', 'speeds': 21, 'frame_material': 'Алюміній',
                'weight': 13.2, 'color': 'Синій/Білий',
                'age_min': 10, 'age_max': 14,
                'is_featured': True, 'rating': 4.6, 'reviews_count': 54, 'in_stock': True,
            },

            # Дитячі (локальні фото kids-01…07)
            {
                'name': 'Belsize Sport 20" Belt Drive', 'category': kids, 'brand': belsize,
                'price': 12900,
                'short_description': 'Ремінний привід, легкий алюміній',
                'description': 'Преміум дитячий велосипед Belsize Sport: срібляста рама, ремінний привід замість ланцюга (чистіше і простіше в догляді), V-brake, покришки CST, рефлектори на спицях. Одна швидкість — ідеально для навчання.',
                'wheel_size': '20', 'speeds': 1, 'frame_material': 'Алюміній',
                'weight': 8.1, 'color': 'Срібний металік',
                'age_min': 6, 'age_max': 9,
                'is_featured': True, 'is_new': True, 'rating': 4.85, 'reviews_count': 28, 'in_stock': True,
                'image_url': '/media/products/kids/kids-01.png',
            },
            {
                'name': 'Youthkkee Balance 12" Рожевий', 'category': kids, 'brand': youthkkee,
                'price': 4200,
                'short_description': 'Біговел без педалей',
                'description': 'Балансувальний велосипед для малюків 2–5 років: легка рама, широкі колеса з протектором, номерний щиток на кермі, регулювання сідла. Без педалей — дитина вчиться балансу перед переходом на повноцінний байк.',
                'wheel_size': '12', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 3.2, 'color': 'Рожевий пастель',
                'age_min': 2, 'age_max': 5,
                'is_featured': True, 'rating': 4.7, 'reviews_count': 56, 'in_stock': True,
                'image_url': '/media/products/kids/kids-02.png',
            },
            {
                'name': 'Rocker Mini 1080 Fat BMX', 'category': kids, 'brand': rocker,
                'price': 8900,
                'short_description': 'Міні BMX з товстими шинами',
                'description': 'Компактний fat BMX: біла рама з написом 1080, високе кермо, широкі шипасті покришки, пеги на осях для трюків, одна швидкість. Для підлітків і дітей, що люблять стант-райдинг.',
                'wheel_size': '16', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 9.5, 'color': 'Білий / блакитні акценти',
                'age_min': 8, 'age_max': 14,
                'is_featured': False, 'rating': 4.55, 'reviews_count': 19, 'in_stock': True,
                'image_url': '/media/products/kids/kids-03.png',
            },
            {
                'name': 'Cubsala Crossed BMX 20"', 'category': kids, 'brand': cubsala,
                'price': 7800,
                'short_description': 'Дитячий BMX, підніжка',
                'description': 'Білий BMX Cubsala з чорними компонентами: класична геометрія, одна швидкість, задній гальмо, рефлектори на колесах, підніжка в комплекті. Універсально для двору та скейтпарку.',
                'wheel_size': '20', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 11.2, 'color': 'Білий',
                'age_min': 7, 'age_max': 13,
                'is_featured': True, 'rating': 4.68, 'reviews_count': 41, 'in_stock': True,
                'image_url': '/media/products/kids/kids-04.png',
            },
            {
                'name': 'Fatboy Mini BMX White Gold', 'category': kids, 'brand': fatboy,
                'price': 11200,
                'short_description': 'Золоті ободи та ланцюг',
                'description': 'Fatboy Mini BMX: біла рама з декором Fatboy, хромоване кермо, дуже широкі покришки, золотисті ободи і ланцюг, стильне сідло з принтом BMX. Заднє гальмо, одна передача.',
                'wheel_size': '16', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 9.8, 'color': 'Білий / золото',
                'age_min': 8, 'age_max': 14,
                'is_featured': True, 'is_new': True, 'rating': 4.8, 'reviews_count': 14, 'in_stock': True,
                'image_url': '/media/products/kids/kids-05.png',
            },
            {
                'name': 'Verde Indigo 18" BMX', 'category': kids, 'brand': verde,
                'price': 9200,
                'short_description': 'BMX 18", темно-синій металік',
                'description': 'Юнацький BMX з рамою темно-синього кольору з переливом, високим кермом, широкими покришками, заднім U-brake, бронзовим ланцюгом. Геометрія з низьким перетином рами для зручної посадки.',
                'wheel_size': '18', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 10.8, 'color': 'Темно-синій металік',
                'age_min': 6, 'age_max': 12,
                'is_featured': False, 'rating': 4.62, 'reviews_count': 22, 'in_stock': True,
                'image_url': '/media/products/kids/kids-06.png',
            },
            {
                'name': 'Colony Horizon 20" BMX Orange', 'category': kids, 'brand': colony,
                'price': 10500,
                'short_description': 'Яскравий BMX Colony',
                'description': 'BMX Colony з помаранчевою рамою та білим логотипом: високе кермо, шипасті покришки, заднє гальмо, рефлектори на педалях. Легка і міцна конструкція для фрістайлу та катання по місту.',
                'wheel_size': '20', 'speeds': 1, 'frame_material': 'Сталь',
                'weight': 11.0, 'color': 'Помаранчевий',
                'age_min': 7, 'age_max': 14,
                'is_featured': True, 'rating': 4.75, 'reviews_count': 33, 'in_stock': True,
                'image_url': '/media/products/kids/kids-07.png',
            },
            {
                'name': 'Merida eBig.Nine 400', 'category': electric, 'brand': merida,
                'price': 69000,
                'description': 'Електро-хардтейл 29": мотор Shimano EP6, батарея 630 Wh, запас ходу до 90 км. Трансмісія Deore 11 швидкостей.',
                'wheel_size': '29', 'speeds': 11, 'frame_material': 'Алюміній',
                'weight': 22.0, 'color': 'Срібний',
                'battery_capacity': '630 Wh', 'motor_power': '250 Вт (85 Нм)', 'range_km': 90,
                'is_featured': False, 'rating': 4.6, 'reviews_count': 16, 'in_stock': True,
                'image_url': '/media/products/electric/electric-01.png',
            },
            {
                'name': 'Specialized Turbo Levo SL Comp', 'category': electric, 'brand': specialized,
                'price': 125000,
                'description': 'Легкий електро-MTB: мотор Specialized SL 1.2, батарея 320 Wh + можливість range extender. Карбонова рама, підвіска 150/150 мм.',
                'wheel_size': '29', 'speeds': 12, 'frame_material': 'Карбон',
                'weight': 18.2, 'color': 'Саган колекція',
                'battery_capacity': '320 Wh', 'motor_power': '240 Вт', 'range_km': 75,
                'is_featured': True, 'is_new': True, 'rating': 4.9, 'reviews_count': 8, 'in_stock': True,
                'image_url': '/media/products/catalog/user-06.png',
            },
            {
                'name': 'Giant Roam E+ 2', 'category': electric, 'brand': giant,
                'price': 62000,
                'description': 'Міський крос-електро: SyncDrive Life, батарея EnergyPak 500 Wh, передня підвіска 63 мм, крила та багажник у комплекті.',
                'wheel_size': '28', 'speeds': 9, 'frame_material': 'Алюміній',
                'weight': 24.3, 'color': 'Темно-синій',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт', 'range_km': 85,
                'is_featured': False, 'rating': 4.5, 'reviews_count': 21, 'in_stock': True,
                'image_url': '/media/products/catalog/user-10.png',
            },

            # Електро (локальні фото electric-09…16)
            {
                'name': 'Specialized Turbo Creo SL Comp Carbon', 'category': electric, 'brand': specialized,
                'price': 198000,
                'short_description': 'Е-гравій: інтегрована батарея, Roval',
                'description': 'Електрогравій Specialized: кремова рама з гранітним напиленням, мотор біля каретки, трансмісія 1x з широкою касетою, колеса Roval, покришки Tracer Pro, дроп-пост, гідравлічні диски. Для асфальту та гравію з підсиленням.',
                'wheel_size': '700c', 'speeds': 12, 'frame_material': 'Карбон',
                'weight': 14.2, 'color': 'Кремовий граніт',
                'battery_capacity': '320 Wh', 'motor_power': '240 Вт', 'range_km': 120,
                'is_featured': True, 'is_new': True, 'rating': 4.92, 'reviews_count': 9, 'in_stock': True,
                'image_url': '/media/products/electric/electric-09.png',
            },
            {
                'name': 'Leitner Tyranno Fat E-MTB 26"', 'category': electric, 'brand': leitner,
                'price': 58900,
                'short_description': 'Fat bike, мотор у задньому колесі',
                'description': 'Білий електрофетбайк Leitner: акумулятор на рамі, задній hub motor, амортизаційна вилка, дискові гальма, широкі шини для піску та снігу, фара та підніжка.',
                'wheel_size': '26', 'speeds': 7, 'frame_material': 'Алюміній',
                'weight': 24.0, 'color': 'Білий',
                'battery_capacity': '504 Wh', 'motor_power': '250 Вт', 'range_km': 55,
                'is_featured': True, 'rating': 4.65, 'reviews_count': 31, 'in_stock': True,
                'image_url': '/media/products/electric/electric-10.png',
            },
            {
                'name': 'Leitner Fold Duo Susp 20"', 'category': electric, 'brand': leitner,
                'price': 49800,
                'short_description': 'Складаний електро, подвійна підвіска',
                'description': 'Складаний e-bike з амортизатором ззаду та MOZO спереду, батарея за сідлом, Shimano трансмісія, диски, багажник і крила. Компактне зберігання в квартирі та багажнику авто.',
                'wheel_size': '20', 'speeds': 7, 'frame_material': 'Алюміній',
                'weight': 22.5, 'color': 'Білий',
                'battery_capacity': '360 Wh', 'motor_power': '250 Вт', 'range_km': 45,
                'is_featured': False, 'rating': 4.58, 'reviews_count': 18, 'in_stock': True,
                'image_url': '/media/products/electric/electric-11.png',
            },
            {
                'name': 'Leitner Voyager Fold Fat 20"', 'category': electric, 'brand': leitner,
                'price': 52900,
                'short_description': 'Складний fat, батарея в рамі',
                'description': 'Низький крок, складана рама, інтегрована батарея в даунтубі, жирні покришки Chao Yang, 7 швидкостей, дискові гальма, багажник і крила. Для міста та легкого off-road.',
                'wheel_size': '20', 'speeds': 7, 'frame_material': 'Алюміній',
                'weight': 23.2, 'color': 'Кремовий',
                'battery_capacity': '480 Wh', 'motor_power': '250 Вт', 'range_km': 50,
                'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 22, 'in_stock': True,
                'image_url': '/media/products/electric/electric-12.png',
            },
            {
                'name': 'Leitner Metro Fold Front 16"', 'category': electric, 'brand': leitner,
                'price': 45900,
                'short_description': 'Компактний складний, мотор спереду',
                'description': 'Міський складаний електро з мотором у передньому колесі, батарея в підсідельному штирі, одна швидкість з захистом зірки, крила та фара. Мінімальний розмір у складеному вигляді.',
                'wheel_size': '16', 'speeds': 1, 'frame_material': 'Алюміній',
                'weight': 18.0, 'color': 'Білий глянець',
                'battery_capacity': '252 Wh', 'motor_power': '250 Вт', 'range_km': 35,
                'is_featured': False, 'rating': 4.5, 'reviews_count': 14, 'in_stock': True,
                'image_url': '/media/products/electric/electric-13.png',
            },
            {
                'name': 'Leichten Trail E-Full 29"', 'category': electric, 'brand': leichten,
                'price': 142000,
                'short_description': 'Повний підвіс e-MTB, Maxxis Minion',
                'description': 'Повнопідвісний електро-MTB: мотор біля каретки, батарея в даунтубі, підвіска спереду і ззаду, 1x привід, гідравлічні диски, покришки Maxxis Minion DHF. Для трейлів і bike park.',
                'wheel_size': '29', 'speeds': 12, 'frame_material': 'Алюміній',
                'weight': 23.8, 'color': 'Білий / графіт',
                'battery_capacity': '630 Wh', 'motor_power': '250 Вт (85 Нм)', 'range_km': 85,
                'is_featured': True, 'rating': 4.88, 'reviews_count': 11, 'in_stock': True,
                'image_url': '/media/products/electric/electric-14.png',
            },
            {
                'name': 'Alwaybike City Step E+ 28"', 'category': electric, 'brand': alwaybike,
                'price': 54900,
                'short_description': 'Крокова рама, MOZO, багажник',
                'description': 'Комфортний міський електро: низька рама, акумулятор на сідловій трубі, задній hub motor, вилка MOZO, дискові гальма, широкі шини, коричневе сідло та гріпи, крила та багажник.',
                'wheel_size': '28', 'speeds': 7, 'frame_material': 'Алюміній',
                'weight': 25.5, 'color': 'Білий',
                'battery_capacity': '500 Wh', 'motor_power': '250 Вт', 'range_km': 70,
                'is_featured': True, 'rating': 4.72, 'reviews_count': 17, 'in_stock': True,
                'image_url': '/media/products/electric/electric-15.png',
            },
            {
                'name': 'Lekker Amsterdam Belt Drive E+', 'category': electric, 'brand': lekker,
                'price': 115000,
                'short_description': 'Ремінний привід, Schwalbe G-One',
                'description': 'Преміум міський e-bike: сіра матова рама з інтегрованою батареєю, мотор біля каретки, карбоновий ремінний привід замість ланцюга, покришки Schwalbe G-One Allround, гідравлічні диски, крила, зручне кермо Dutch-style.',
                'wheel_size': '28', 'speeds': 8, 'frame_material': 'Алюміній',
                'weight': 21.0, 'color': 'Сірий мат',
                'battery_capacity': '504 Wh', 'motor_power': '250 Вт', 'range_km': 95,
                'is_featured': True, 'is_new': True, 'rating': 4.9, 'reviews_count': 8, 'in_stock': True,
                'image_url': '/media/products/electric/electric-16.png',
            },
        ]

        for b in bikes:
            img = b.get('image_url', '')
            if not (isinstance(img, str) and img.startswith('/media/')):
                b['image_url'] = pick_themed_image(b['category'].slug, b['name'])

        for b in bikes:
            name = b['name']
            defaults = dict(b)
            defaults.pop('name', None)
            self.upsert_product(name=name, defaults=defaults)

    def create_gear(self):
        helmet_cat = Category.objects.get(slug='helmet')
        clothing_cat = Category.objects.get(slug='clothing')
        glasses_cat = Category.objects.get(slug='glasses')
        shoes_cat = Category.objects.get(slug='shoes')
        gloves_cat = Category.objects.get(slug='gloves')
        lights_cat = Category.objects.get(slug='lights')
        locks_cat = Category.objects.get(slug='locks')
        bags_cat = Category.objects.get(slug='bags')
        tools_cat = Category.objects.get(slug='tools')
        accessories_cat = Category.objects.get(slug='accessories')

        gear_items = [
            # Шоломи — локальні фото helmet-01…10
            {
                'name': 'Kask Protone білий матовий', 'category': helmet_cat,
                'price': 9200,
                'description': 'Шосейний шолом з вентиляцією та легким корпусом, регульована система затягування, для довгих виходів.',
                'color': 'Білий матовий', 'weight': 0.25,
                'is_featured': True, 'rating': 4.85, 'reviews_count': 142, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-01.png',
            },
            {
                'name': 'MET Rivale білий глянець', 'category': helmet_cat,
                'price': 5600,
                'description': 'Аеродинамічний шолом MET з великими каналами вентиляції, глянцеве біле покриття.',
                'color': 'Білий глянець', 'weight': 0.24,
                'is_featured': True, 'rating': 4.72, 'reviews_count': 98, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-02.png',
            },
            {
                'name': 'Urban Bowl шолом білий', 'category': helmet_cat,
                'price': 1890,
                'description': 'Класичний міський / мультиспорт шолом з округлою оболонкою, регульовані ремені, матовий білий.',
                'color': 'Білий матовий', 'weight': 0.35,
                'is_featured': False, 'rating': 4.5, 'reviews_count': 210, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-03.png',
            },
            {
                'name': 'Aero Silver шолом', 'category': helmet_cat,
                'price': 6400,
                'description': 'Сріблястий аерошолом з розвиненою вентиляцією, обтічний силует для шосе та крос-кантрі.',
                'color': 'Сріблястий', 'weight': 0.27,
                'is_featured': True, 'rating': 4.78, 'reviews_count': 76, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-04.png',
            },
            {
                'name': 'MTB Trail помаранчевий з козирком', 'category': helmet_cat,
                'price': 4200,
                'description': 'Гірський шолом з інтегрованим козирком, агресивна вентиляція, яскравий помаранчевий колір для трейлу.',
                'color': 'Помаранчевий', 'weight': 0.32,
                'is_featured': True, 'is_new': True, 'rating': 4.68, 'reviews_count': 54, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-05.png',
            },
            {
                'name': 'MET Manta білий/чорний', 'category': helmet_cat,
                'price': 7200,
                'description': 'Шосейний MET з контрастними чорними каналами вентиляції та білим корпусом, гоночний профіль.',
                'color': 'Білий/чорний', 'weight': 0.26,
                'is_featured': True, 'rating': 4.81, 'reviews_count': 61, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-06.png',
            },
            {
                'name': 'Silverbird вентильований шолом', 'category': helmet_cat,
                'price': 5900,
                'description': 'Сріблястий шолом з «ребристою» вентиляцією, легка оправа та зручний ремінь.',
                'color': 'Сріблястий глянець', 'weight': 0.28,
                'is_featured': False, 'rating': 4.65, 'reviews_count': 43, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-07.png',
            },
            {
                'name': 'Шолом шосейний MIPS білий', 'category': helmet_cat,
                'price': 5100,
                'description': 'Шосейний шолом з системою MIPS, білий глянець, чорні ремені та вентиляційні канали.',
                'color': 'Білий', 'weight': 0.29,
                'is_featured': True, 'rating': 4.74, 'reviews_count': 128, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-08.png',
            },
            {
                'name': 'Шолом шосейний MIPS профіль', 'category': helmet_cat,
                'price': 5100,
                'description': 'Білий шолом з MIPS у профільному ракурсі, велика зона вентиляції та комфортна посадка.',
                'color': 'Білий', 'weight': 0.29,
                'is_featured': False, 'rating': 4.74, 'reviews_count': 119, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-09.png',
            },
            {
                'name': 'HJC Ibex білий шосейний', 'category': helmet_cat,
                'price': 6800,
                'description': 'Шосейний шолом HJC з аеродинамічними вентилями та легким корпусом, глянцевий білий.',
                'color': 'Білий глянець', 'weight': 0.25,
                'is_featured': True, 'rating': 4.79, 'reviews_count': 87, 'in_stock': True,
                'image_url': '/media/products/helmets/helmet-10.png',
            },
            # Велоформа — локальні фото clothing-01…07
            {
                'name': 'SYN Global білі бібшорти', 'category': clothing_cat,
                'price': 3490,
                'description': 'Білі бібшорти з логотипом SYN, ребристий матеріал, лямки з написом Global Cycling Club, гоночний крій. чоловіча велоформа.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.72, 'reviews_count': 56, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-01.png',
            },
            {
                'name': 'Resting Cycling Face комплект', 'category': clothing_cat,
                'price': 5290,
                'description': 'Ретро-комплект: джерсі з принтом Resting Cycling Face та бібшорти в жовто-чорній гамі, короткий рукав. чоловіча велоформа.',
                'color': 'Жовтий/чорний', 'is_featured': True, 'is_new': True, 'rating': 4.81, 'reviews_count': 34, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-02.png',
            },
            {
                'name': 'SYN бібшорти білий профіль', 'category': clothing_cat,
                'price': 3590,
                'description': 'Білі бібшорти SYN у тричвертному ракурсі, технічний лайкра, бирка на стегні. чоловіча велоформа.',
                'color': 'Білий', 'is_featured': False, 'rating': 4.68, 'reviews_count': 41, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-03.png',
            },
            {
                'name': 'Бібшорти перфорація біло-чорні', 'category': clothing_cat,
                'price': 3890,
                'description': 'Бібшорти з білою верхньою частиною та чорними шортами, лазерна перфорація на поясі, анатомічний chamois. чоловіча велоформа.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.75, 'reviews_count': 48, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-04.png',
            },
            {
                'name': 'Комплект довгий рукав градієнт', 'category': clothing_cat,
                'price': 6490,
                'description': 'Довгорукавне джерсі з градієнтом білий–чорний і бібшорти з білими манжетами, три кишені ззаду.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.77, 'reviews_count': 29, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-05.png',
            },
            {
                'name': 'Team Sky Castelli комплект', 'category': clothing_cat,
                'price': 8990,
                'description': 'Офіційний стиль команди: довгий рукав з брендингом sky, шорти Castelli з логотипом на стегнах.',
                'color': 'Білий/синій/чорний', 'is_featured': True, 'rating': 4.88, 'reviews_count': 62, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-06.png',
            },
            {
                'name': 'SYN Global білі з акцентами', 'category': clothing_cat,
                'price': 3690,
                'description': 'Білі бібшорти SYN з рожево-бірюзовими акцентами на стегнах, лямки з текстом Global Cycling Club.',
                'color': 'Білий/рожевий/бірюза', 'is_featured': False, 'rating': 4.7, 'reviews_count': 37, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-07.png',
            },
            # Дитяча велоформа — локальні фото clothing-kids-01…04
            {
                'name': 'Дитяча велоформа синя (комплект)', 'category': clothing_cat,
                'price': 2490,
                'description': 'Комплект велоформи для дітей: джерсі та шорти. дитяча велоформа.',
                'color': 'Синій', 'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 12, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-kids-01.png',
            },
            {
                'name': 'Дитяча велоформа кольорова (комплект)', 'category': clothing_cat,
                'price': 2590,
                'description': 'Яскравий дитячий комплект: джерсі та шорти, дихаюча тканина. дитяча велоформа.',
                'color': 'Мікс', 'is_featured': True, 'rating': 4.6, 'reviews_count': 9, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-kids-02.png',
            },
            {
                'name': 'Дитяча велоформа біло-рожева (комплект)', 'category': clothing_cat,
                'price': 2690,
                'description': 'Дитячий комплект велоформи: легке джерсі та шорти з анатомічною вставкою. дитяча велоформа.',
                'color': 'Білий/рожевий', 'is_featured': True, 'rating': 4.7, 'reviews_count': 11, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-kids-03.png',
            },
            {
                'name': 'Дитяча велоформа синя (джерсі)', 'category': clothing_cat,
                'price': 1790,
                'description': 'Дитяче джерсі для тренувань: комфортний крій, три кишені ззаду. дитяча велоформа.',
                'color': 'Синій', 'is_featured': False, 'rating': 4.5, 'reviews_count': 6, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-kids-04.png',
            },
            # Жіноча велоформа — локальні фото clothing-women-01…06
            {
                'name': 'Жіноча велоформа чорна з акцентами (комплект)', 'category': clothing_cat,
                'price': 2890,
                'description': 'Жіночий комплект: джерсі + шорти, приталений крій. жіноча велоформа.',
                'color': 'Чорний', 'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 14, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-women-01.png',
            },
            {
                'name': 'Жіноча велоформа геометрія (комплект)', 'category': clothing_cat,
                'price': 2990,
                'description': 'Комплект з геометричним принтом: дихаюче джерсі та шорти. жіноча велоформа.',
                'color': 'Блакитний/мульти', 'is_featured': True, 'is_new': True, 'rating': 4.6, 'reviews_count': 10, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-women-02.png',
            },
            {
                'name': 'Жіноча велоформа бордо (комплект)', 'category': clothing_cat,
                'price': 3090,
                'description': 'Комфортний комплект у бордо: еластична тканина, кишені ззаду. жіноча велоформа.',
                'color': 'Бордо/чорний', 'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 12, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-women-03.png',
            },
            {
                'name': 'Жіноча велоформа фіолетова (комплект)', 'category': clothing_cat,
                'price': 3190,
                'description': 'Фіолетовий комплект: джерсі та бібшорти, м’яка вставка. жіноча велоформа.',
                'color': 'Фіолетовий', 'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 9, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-women-04.png',
            },
            {
                'name': 'Жіноча велоформа рожево-бірюзова (комплект)', 'category': clothing_cat,
                'price': 3290,
                'description': 'Яскравий комплект: джерсі + бібшорти, приталена посадка. жіноча велоформа.',
                'color': 'Рожевий/бірюза', 'is_featured': True, 'is_new': True, 'rating': 4.8, 'reviews_count': 16, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-women-05.png',
            },
            {
                'name': 'Жіноча велоформа сіра (комплект)', 'category': clothing_cat,
                'price': 2790,
                'description': 'Легкий комплект у сірій гамі: джерсі та шорти для тренувань. жіноча велоформа.',
                'color': 'Сірий/чорний', 'is_featured': True, 'is_new': True, 'rating': 4.6, 'reviews_count': 8, 'in_stock': True,
                'image_url': '/media/products/clothing/clothing-women-06.png',
            },
            # Вело-туфлі — локальні фото shoes-01…09
            {
                'name': 'Shimano S-PHYRE XC білі', 'category': shoes_cat,
                'price': 11200,
                'description': 'Shimano S-PHYRE для MTB/XC: подвійний BOA®, білий перфорований верх, шиповка під гравій і крос-кантрі. жіночі вело-туфлі.',
                'color': 'Білий', 'is_featured': True, 'rating': 4.86, 'reviews_count': 71, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-01.png',
            },
            {
                'name': 'Sunlest шосейні білий/чорний', 'category': shoes_cat,
                'price': 4200,
                'description': 'Шосейні туфлі Sunlest: два роторні замки, білий верх з перфорацією, контрастна п\'ята. жіночі вело-туфлі.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.64, 'reviews_count': 45, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-02.png',
            },
            {
                'name': 'Santic шосейні пара білий/червоний', 'category': shoes_cat,
                'price': 3890,
                'description': 'Пара шосейних туфель Santic з Atop, червоні акценти в сітці, жорстка підошва під 3-болт. жіночі вело-туфлі.',
                'color': 'Білий/червоний', 'is_featured': True, 'is_new': True, 'rating': 4.7, 'reviews_count': 52, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-03.png',
            },
            {
                'name': 'Santic Atop білий візерунок', 'category': shoes_cat,
                'price': 3990,
                'description': 'Santic з подвійним Atop, білий верх з гексагоном, чорні вставки та шнурівка тросами. чоловічі вело-туфлі.',
                'color': 'Білий/чорний', 'is_featured': False, 'rating': 4.72, 'reviews_count': 38, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-04.png',
            },
            {
                'name': 'Mavic Cosmic SLR білий/сірий', 'category': shoes_cat,
                'price': 9800,
                'description': 'Mavic Cosmic SLR: градієнт білий–сірий, подвійний BOA®, гоночний профіль для шосе. чоловічі вело-туфлі.',
                'color': 'Білий/сірий', 'is_featured': True, 'rating': 4.84, 'reviews_count': 59, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-05.png',
            },
            {
                'name': 'Northwave шосейні білі SLW3', 'category': shoes_cat,
                'price': 5600,
                'description': 'Northwave: ротор SLW3, липучка на носі, перфорація, чорна підошва та логотип nw. чоловічі вело-туфлі.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.69, 'reviews_count': 63, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-06.png',
            },
            {
                'name': 'GAERNE шосейні білі BOA', 'category': shoes_cat,
                'price': 8900,
                'description': 'GAERNE: подвійний BOA®, білий верх з лазерною перфорацією, чорна п\'ята та підошва. дитячі вело-туфлі.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.81, 'reviews_count': 47, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-07.png',
            },
            {
                'name': "fi'zi:k шосейні біло-сині з лаймом", 'category': shoes_cat,
                'price': 9200,
                'description': "fi'zi:k: подвійний BOA, білий mesh, темно-сині панелі та неоново-жовті вставки. дитячі вело-туфлі.",
                'color': 'Білий/синій/лайм', 'is_featured': True, 'rating': 4.83, 'reviews_count': 55, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-08.png',
            },
            {
                'name': "fi'zi:k шосейні BOA профіль", 'category': shoes_cat,
                'price': 9200,
                'description': "fi'zi:k шосейні туфлі з BOA, біло-синя гама та лайм-акценти — альтернативний ракурс. дитячі вело-туфлі.",
                'color': 'Білий/синій/лайм', 'is_featured': False, 'rating': 4.83, 'reviews_count': 41, 'in_stock': True,
                'image_url': '/media/products/shoes/shoes-09.png',
            },
            # Ліхтарі — локальні фото lights-01…11
            {
                'name': 'Kensington хром передній ретро', 'category': lights_cat,
                'price': 1890,
                'description': 'Ретро-фара «куля» на хромі, сітчаста лінза, кріплення на вилку. Стиль міста та круїзерів Kensington.',
                'color': 'Хром/білий', 'is_featured': True, 'rating': 4.71, 'reviews_count': 88, 'in_stock': True,
                'image_url': '/media/products/lights/lights-01.png',
            },
            {
                'name': 'PLAZMA задній LED вертикальний', 'category': lights_cat,
                'price': 690,
                'description': 'Компактний задній ліхтар PLAZMA: чорний корпус, червона лінза, COB-смуга, кліпса на підсідел.',
                'color': 'Чорний/червоний', 'is_featured': True, 'rating': 4.58, 'reviews_count': 124, 'in_stock': True,
                'image_url': '/media/products/lights/lights-02.png',
            },
            {
                'name': 'BUCKLOS круглий передній COB', 'category': lights_cat,
                'price': 890,
                'description': 'Круглий передній BUCKLOS: жовті LED, алмазна оптика, кнопка живлення, кріплення на кермо.',
                'color': 'Чорний/срібний', 'is_featured': True, 'is_new': True, 'rating': 4.64, 'reviews_count': 67, 'in_stock': True,
                'image_url': '/media/products/lights/lights-03.png',
            },
            {
                'name': 'BUCKLOS кіт передній і задній', 'category': lights_cat,
                'price': 1490,
                'description': 'Набір BUCKLOS: передній і задній круглі ліхтарі, ремені, два USB-кабелі для зарядки.',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.7, 'reviews_count': 91, 'in_stock': True,
                'image_url': '/media/products/lights/lights-04.png',
            },
            {
                'name': 'ROCKBROS передній круглий USB-C', 'category': lights_cat,
                'price': 790,
                'description': 'ROCKBROS: круглий передній ліхтар, ремінь-кріплення, білий USB-C кабель у комплекті.',
                'color': 'Чорний', 'is_featured': False, 'rating': 4.62, 'reviews_count': 201, 'in_stock': True,
                'image_url': '/media/products/lights/lights-05.png',
            },
            {
                'name': 'ROCKBROS задній з ременем USB-C', 'category': lights_cat,
                'price': 750,
                'description': 'Задній ROCKBROS: червона лінза, фактурне кільце, зарядка USB-C, гумовий ремінь.',
                'color': 'Чорний/червоний', 'is_featured': False, 'rating': 4.6, 'reviews_count': 156, 'in_stock': True,
                'image_url': '/media/products/lights/lights-06.png',
            },
            {
                'name': 'ROCKBROS задній COB круглий', 'category': lights_cat,
                'price': 790,
                'description': 'Потужний задній ROCKBROS: червоне кільце та яскраве ядро LED, видимість у місті та трейлі.',
                'color': 'Чорний/червоний', 'is_featured': True, 'rating': 4.66, 'reviews_count': 178, 'in_stock': True,
                'image_url': '/media/products/lights/lights-07.png',
            },
            {
                'name': 'Набір LED перед+зад водостійкий', 'category': lights_cat,
                'price': 1290,
                'description': 'Прямокутні передній і задній ліхтарі, 6 LED кожен, Y-кабель USB для зарядки, захист від вологи.',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.73, 'reviews_count': 142, 'in_stock': True,
                'image_url': '/media/products/lights/lights-08.png',
            },
            {
                'name': 'Smiling Shark подвійний LED дисплей', 'category': lights_cat,
                'price': 1190,
                'description': 'Smiling Shark: два LED-об\'єктиви, дисплей заряду %, інтегроване кріплення на кермо.',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.69, 'reviews_count': 99, 'in_stock': True,
                'image_url': '/media/products/lights/lights-09.png',
            },
            {
                'name': 'Smiling Shark передній дисплей профіль', 'category': lights_cat,
                'price': 1190,
                'description': 'Та сама модель Smiling Shark у профільному ракурсі: подвійна оптика та екран заряду.',
                'color': 'Чорний', 'is_featured': False, 'rating': 4.69, 'reviews_count': 54, 'in_stock': True,
                'image_url': '/media/products/lights/lights-10.png',
            },
            {
                'name': 'VICTGOAL набір на кермі', 'category': lights_cat,
                'price': 1690,
                'description': 'VICTGOAL: передній і задній на одному ряді керма, срібні панелі, боковий червоний маркер.',
                'color': 'Чорний/срібний', 'is_featured': True, 'rating': 4.76, 'reviews_count': 73, 'in_stock': True,
                'image_url': '/media/products/lights/lights-11.png',
            },
            # Locks
            {
                'name': 'Kryptonite Evolution Mini-7 U-lock', 'category': locks_cat,
                'price': 2490,
                'description': 'U-замок з загартованої сталі. Високий рівень захисту для міста.',
                'color': 'Жовтий/Чорний', 'is_featured': True, 'rating': 4.7, 'reviews_count': 98, 'in_stock': True,
            },
            {
                'name': 'Abus Tresor 1385 Ланцюг-замок', 'category': locks_cat,
                'price': 1890, 'old_price': 2190,
                'description': 'Ланцюг 6 мм з текстильним чохлом. Кодове блокування, зручно для щоденного використання.',
                'color': 'Чорний', 'is_featured': False, 'rating': 4.5, 'reviews_count': 76, 'in_stock': True,
            },
            # Bags
            # Вело-сумки — локальні фото bags-01…09
            {
                'name': 'Cyclite підсідельна bikepacking сіра', 'category': bags_cat,
                'price': 2490,
                'short_description': (
                    'Водонепроникна підсідельна сумка з roll-top, щоб волога не потрапляла всередину, і двома варіантами закриття '
                    '(зверху або збоку). Оновлений адаптер для надійного кріплення під сідлом. Світловідбиваючі елементи безпеки.'
                ),
                'description': (
                    'Підсідельна сумка Cyclite: світло-сірий корпус, roll-top, червона пряжка, банджі зверху, клапан для стиснення повітря. '
                    'Підходить для bikepacking та довгих днів у сідлі.'
                ),
                'bag_features': (
                    'Водонепроникна конструкція\n'
                    'Roll-top із двома варіантами закриття (зверху або збоку)\n'
                    'Сумісність з типовими адаптерами під сідло / рейки\n'
                    'Світловідбиваючі вставки\n'
                    'Максимальне навантаження до 12 кг\n'
                    'Внутрішні кишені-органайзери\n'
                    'Основне відділення для інструментів і запасів'
                ),
                'bag_volume': '20 л',
                'bag_weight_note': '500 г',
                'bag_dimensions': 'Висота: 20–35 см\nШирина: 30 см\nГлибина: 16 см',
                'color': 'Сірий/чорний', 'is_featured': True, 'rating': 4.78, 'reviews_count': 61, 'in_stock': True,
                'image_url': '/media/products/bags/bags-01.png',
            },
            {
                'name': 'Cyclite сумка в раму біла', 'category': bags_cat,
                'price': 2190,
                'short_description': (
                    'Сумка у трикутник рами для tube й дрібного інструменту: легкий синтетичний матеріал, надійні липучки та блискавка.'
                ),
                'description': 'Сумка у трикутник рами Cyclite: білий технічний матеріал, чорна блискавка з червоним пуллером, три липучки.',
                'bag_features': (
                    'Призначення: трикутник рами (frame bag)\n'
                    'Водовідштовхувальний текстиль\n'
                    'Головна блискавка з червоним пуллером\n'
                    'Три липучки для фіксації до труб рами\n'
                    'Основне відділення для камери, ключа, енергетиків'
                ),
                'bag_volume': '4 л',
                'bag_weight_note': '280 г',
                'bag_dimensions': 'Внутрішня довжина: 38 см\nВисота (біля штиря): 12 см\nГлибина: 5 см',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.74, 'reviews_count': 48, 'in_stock': True,
                'image_url': '/media/products/bags/bags-02.png',
            },
            {
                'name': 'Cyclite frame pack сітка рефлектор', 'category': bags_cat,
                'price': 2290,
                'short_description': 'Frame pack з зовнішньою сіткою та рефлектором — зручно для дрібниць і фляги на гравії чи шосе.',
                'description': 'Frame pack Cyclite: зовнішня сітка-карман, рефлекторна смуга, водовідштовхувальна блискавка.',
                'bag_features': (
                    'Топ-труб / рама — універсальне кріплення\n'
                    'Зовнішній сітчастий кишеню для дрібниць\n'
                    'Рефлекторна смуга для видимості\n'
                    'Водовідштовхувальна блискавка\n'
                    'Легкий доступ під час руху'
                ),
                'bag_volume': '3,5 л',
                'bag_weight_note': '310 г',
                'bag_dimensions': 'Довжина: 35 см\nШирина: 6 см\nВисота: 12 см',
                'color': 'Сірий/білий', 'is_featured': False, 'rating': 4.71, 'reviews_count': 35, 'in_stock': True,
                'image_url': '/media/products/bags/bags-03.png',
            },
            {
                'name': 'ROCKBROS барна олива на кермі', 'category': bags_cat,
                'price': 1890,
                'short_description': 'Барна сумка на дроп-бар для телефону, перекусу й лайтера — швидкий доступ на маршруті.',
                'description': 'Барна сумка ROCKBROS на дроп-барі: оливковий текстиль, помаранчева банджі-сітка на фронті.',
                'bag_features': (
                    'Кріплення на дроп-бар / літаючий топ\n'
                    'Текстиль із підвищеною зносостійкістю\n'
                    'Фронтова банджі-сітка для рукавичок / дрібниць\n'
                    'Внутрішній розділювач (за моделлю)\n'
                    'Блискавка по всій довжині для доступу зверху'
                ),
                'bag_volume': '2,8 л',
                'bag_weight_note': '195 г',
                'bag_dimensions': 'Довжина: 24 см\nДіаметр: 11 см',
                'color': 'Оливковий', 'is_featured': True, 'is_new': True, 'rating': 4.69, 'reviews_count': 112, 'in_stock': True,
                'image_url': '/media/products/bags/bags-04.png',
            },
            {
                'name': 'LEAD OUT барна біла burrito', 'category': bags_cat,
                'price': 1590,
                'short_description': 'Циліндрична «burrito» на кермо — мінімальна вага й об’єм для щоденних поїздок.',
                'description': 'Циліндрична сумка на кермо LEAD OUT: білий корпус, чорні ремені та блискавка, бірка бренду.',
                'bag_features': (
                    'Компактний формат під дроп-бар\n'
                    'Ripstop верхній шар\n'
                    'Чорні стропи та блискавка YKK\n'
                    'Логобірка бренду на фронті\n'
                    'Для телефону в чохлі, ключів, снеків'
                ),
                'bag_volume': '2,2 л',
                'bag_weight_note': '165 г',
                'bag_dimensions': 'Довжина: 22 см\nДіаметр: 10 см',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.65, 'reviews_count': 77, 'in_stock': True,
                'image_url': '/media/products/bags/bags-05.png',
            },
            {
                'name': 'Барна сумка чорна на руль', 'category': bags_cat,
                'price': 1990,
                'short_description': 'Універсальна чорна барна сумка з боковими блискавками та місцем під карти чи телефон.',
                'description': 'Чорна барна сумка на дроп-бари: ripstop і гладкий шар, срібна смуга, бокові блискавки, петлі для кріплення.',
                'bag_features': (
                    'Ripstop + гладкий поліестер\n'
                    'Бокові блискавки для доступу без знімання\n'
                    'Срібна світловідбиваюча смуга\n'
                    'Петлі під додатковий ремінь\n'
                    'Максимум комфорту на gravel і шосе'
                ),
                'bag_volume': '3 л',
                'bag_weight_note': '210 г',
                'bag_dimensions': 'Довжина: 26 см\nШирина (фронт): 12 см\nВисота: 11 см',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.76, 'reviews_count': 54, 'in_stock': True,
                'image_url': '/media/products/bags/bags-06.png',
            },
            {
                'name': 'Барна біла ripstop bungee', 'category': bags_cat,
                'price': 1690,
                'short_description': 'Біла барна з ромбовим ripstop і банджі спереду — тримає легкий шар одягу або карту.',
                'description': 'Біла циліндрична сумка з ромбовим ripstop, вертикальний ремінь і шнур-банджі на фронті.',
                'bag_features': (
                    'Ромбовий ripstop для стійкості до порізів\n'
                    'Шнур-банджі на фронті для рукавичок\n'
                    'Вертикальний ремінь стягування\n'
                    'Легка конструкція для швидких виїздів\n'
                    'Внутрішній простір без перегородок'
                ),
                'bag_volume': '2,5 л',
                'bag_weight_note': '178 г',
                'bag_dimensions': 'Довжина: 23 см\nДіаметр: 10 см',
                'color': 'Білий/чорний', 'is_featured': False, 'rating': 4.63, 'reviews_count': 89, 'in_stock': True,
                'image_url': '/media/products/bags/bags-07.png',
            },
            {
                'name': 'Барна чорна з сіткою', 'category': bags_cat,
                'price': 1890,
                'short_description': 'Чорна барна з боковою сіткою під пляшку й горизонтальною блискавкою доступу.',
                'description': 'Чорна барна сумка: горизонтальна блискавка, бокова сітка, помаранчева строчка на стропі.',
                'bag_features': (
                    'Горизонтальна блискавка на всю ширину\n'
                    'Бокова сітка під 0,5 л пляшку\n'
                    'Контрастна помаранчева строчка на стропах\n'
                    'Чорний матовий текстиль\n'
                    'Швидкий монтаж на дроп-бар'
                ),
                'bag_volume': '3,2 л',
                'bag_weight_note': '225 г',
                'bag_dimensions': 'Довжина: 25 см\nШирина: 13 см\nВисота: 11 см',
                'color': 'Чорний', 'is_featured': False, 'rating': 4.68, 'reviews_count': 42, 'in_stock': True,
                'image_url': '/media/products/bags/bags-08.png',
            },
            {
                'name': 'Alpkit барна roll-top сіра', 'category': bags_cat,
                'price': 2190,
                'short_description': 'Roll-top барна сумка Alpkit для gravel і шосе — захист від бризок і регульований об’єм.',
                'description': 'Alpkit на кермо gravel/шосе: темно-сірий ripstop, roll-top, банджі та пряжки, логотип alpkit.',
                'bag_features': (
                    'Roll-top закриття від дощу й бруду\n'
                    'Темно-сірий ripstop з підкладкою\n'
                    'Банджі та пряжки для стискання об’єму\n'
                    'Брендований шильдик Alpkit\n'
                    'Для інструменту, їжі та дрібної покришки'
                ),
                'bag_volume': '3,8 л',
                'bag_weight_note': '268 г',
                'bag_dimensions': 'У розкритому roll-top: до 28 см завдовжки\nШирина: 14 см\nВисота: 12 см',
                'color': 'Темно-сірий', 'is_featured': True, 'rating': 4.82, 'reviews_count': 66, 'in_stock': True,
                'image_url': '/media/products/bags/bags-09.png',
            },
            # Tools
            {
                'name': 'Crankbrothers M19 Мультитул', 'category': tools_cat,
                'price': 1290,
                'description': '19 функцій: hex, torx, викрутки, вижимка ланцюга. Компактний і міцний.',
                'color': 'Чорний/Червоний', 'is_featured': True, 'rating': 4.8, 'reviews_count': 287, 'in_stock': True,
            },
            {
                'name': 'Lezyne Pocket Drive Насос', 'category': tools_cat,
                'price': 1090,
                'description': 'Міні-насос до 160 PSI. CNC алюміній, сумісний Presta/Schrader.',
                'color': 'Срібний', 'is_featured': False, 'rating': 4.6, 'reviews_count': 193, 'in_stock': True,
            },
            # Accessories (general)
            {
                'name': 'Elite Custom Race Фляготримач', 'category': accessories_cat,
                'price': 590,
                'description': 'Легкий фляготримач з армованого композиту. Надійно тримає флягу на бездоріжжі.',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.7, 'reviews_count': 412, 'in_stock': True,
            },
            {
                'name': 'Garmin Edge 530 Велокомп\'ютер', 'category': accessories_cat,
                'price': 9990, 'old_price': 11990,
                'description': 'GPS велокомп\'ютер з навігацією, тренуваннями, Strava сегментами. До 20 год автономності.',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.9, 'reviews_count': 523, 'in_stock': True,
            },
            {
                'name': 'Bell Звінок латунний', 'category': accessories_cat,
                'price': 390,
                'description': 'Гучний і стильний дзвінок для міста. Легке кріплення на кермо 22.2–31.8 мм.',
                'color': 'Золотистий', 'is_featured': False, 'rating': 4.4, 'reviews_count': 88, 'in_stock': True,
            },

            # Додаткове екіпірування (різні категорії)
            {
                'name': 'Hiplok Z Lok Combo Замок', 'category': locks_cat,
                'price': 990,
                'description': 'Легкий комбінований трос-замок для коротких зупинок, кольоровий корпус.',
                'color': 'Жовтий', 'is_featured': False, 'rating': 4.3, 'reviews_count': 210, 'in_stock': True,
            },
            {
                'name': 'Park Tool CT-5 Міні-вижимка ланцюга', 'category': tools_cat,
                'price': 890,
                'description': 'Кишенькова вижимка ланцюга для 5–12 швидкостей, закріплена на раму.',
                'color': 'Синій', 'is_featured': True, 'rating': 4.9, 'reviews_count': 340, 'in_stock': True,
            },
            {
                'name': 'Wahoo Elemnt Bolt V2 GPS', 'category': accessories_cat,
                'price': 11200, 'old_price': 12990,
                'description': 'Компактний GPS з навігацією, ANT+ та Bluetooth, інтеграція з Strava та тренуваннями.',
                'color': 'Чорний', 'is_featured': True, 'rating': 4.8, 'reviews_count': 189, 'in_stock': True,
            },
            {
                'name': 'Elite Fly Пляшка 750 мл', 'category': accessories_cat,
                'price': 290,
                'description': 'Легка пляшка з широким горлом, біологічний пластик, без смаку пластику.',
                'color': 'Прозорий/Синій', 'is_featured': False, 'rating': 4.6, 'reviews_count': 501, 'in_stock': True,
            },
            {
                'name': 'Muc-Off Набір для миття велосипеда', 'category': accessories_cat,
                'price': 1890,
                'description': 'Очищувач, губка, щітки, знежирювач ланцюга — повний догляд за байком вдома.',
                'color': 'Набір', 'is_featured': False, 'rating': 4.7, 'reviews_count': 267, 'in_stock': True,
            },

            # Окуляри — лише локальні фото glasses-01, glasses-02
            {
                'name': 'Sport Shield Cyan Mirror', 'category': glasses_cat,
                'price': 3290,
                'description': 'Велоокуляри shield: одна панорамна лінза з бірюзово-синім дзеркальним покриттям, прозора оправа, захист від UV та вітру. Для шосе та MTB.',
                'color': 'Прозора оправа / ціан лінза', 'is_featured': True, 'is_new': True, 'rating': 4.75, 'reviews_count': 42, 'in_stock': True,
                'image_url': '/media/products/glasses/glasses-01.png',
            },
            {
                'name': 'VIF Sport Shield Orange Revo', 'category': glasses_cat,
                'price': 2890,
                'description': 'Спортивні окуляри VIF: біла матова оправа, лінза з градієнтом помаранчево-жовто-зелена, логотип на лінзі, гумові наконечники заушників.',
                'color': 'Білий / рево', 'is_featured': False, 'rating': 4.65, 'reviews_count': 28, 'in_stock': True,
                'image_url': '/media/products/glasses/glasses-02.png',
            },

            # Рукавиці — локальні фото gloves-01…09
            {
                'name': 'SKMT Mesh безпалі рукавиці', 'category': gloves_cat,
                'price': 1490,
                'description': 'Безпалі вело-рукавиці: біла сітка зверху, темна долоня з гелем і перфорацією, зручне знімання.',
                'color': 'Білий/сірий', 'is_featured': True, 'rating': 4.62, 'reviews_count': 88, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-01.png',
            },
            {
                'name': 'GripGrab повнопалі сітка', 'category': gloves_cat,
                'price': 1890,
                'description': 'Повнопалі рукавички GripGrab: перфорована сітка, рефлектори на мізинці, підсилені кінчики пальців.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.71, 'reviews_count': 64, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-02.png',
            },
            {
                'name': 'Leatt 1.0 GripR MTB', 'category': gloves_cat,
                'price': 1390,
                'description': 'Leatt 1.0 GripR: біла сітка, помаранчеві смуги бренду, Micron Grip на долоні, для MTB.',
                'color': 'Білий/помаранчевий', 'is_featured': True, 'is_new': True, 'rating': 4.68, 'reviews_count': 51, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-03.png',
            },
            {
                'name': 'Leatt 4.0 Lite долоня NanoGrip', 'category': gloves_cat,
                'price': 2190,
                'description': 'Leatt 4.0 Lite: вид долоні з NanoGrip, легка сітка, модель для точного контролю керма.',
                'color': 'Білий/сірий', 'is_featured': False, 'rating': 4.74, 'reviews_count': 37, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-04.png',
            },
            {
                'name': 'Leatt 4.0 Lite білий/чорний', 'category': gloves_cat,
                'price': 2290,
                'description': 'Повнопалі Leatt 4.0 Lite: сітка, захист на кістках, NanoGrip, біло-чорна гама.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.79, 'reviews_count': 72, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-05.png',
            },
            {
                'name': 'Cognative MTB Marble', 'category': gloves_cat,
                'price': 1790,
                'description': 'Cognative: мармуровий принт зверху, чорна долоня з помаранчевим брендингом, повнопалі для MTB.',
                'color': 'Сірий/чорний/помаранчевий', 'is_featured': False, 'rating': 4.58, 'reviews_count': 29, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-06.png',
            },
            {
                'name': 'Leatt Mesh верх руки', 'category': gloves_cat,
                'price': 1350,
                'description': 'Leatt: біла сітка, смуги бренду, підсилений великий палець — для теплої погоди.',
                'color': 'Білий/помаранчевий', 'is_featured': False, 'rating': 4.65, 'reviews_count': 41, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-07.png',
            },
            {
                'name': 'Leatt 4.0 Lite чорний сірий', 'category': gloves_cat,
                'price': 2290,
                'description': 'Leatt 4.0 Lite у темній гамі: 3DF на кістках, сірий NanoGrip, повнопалі.',
                'color': 'Чорний/сірий', 'is_featured': True, 'rating': 4.77, 'reviews_count': 58, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-08.png',
            },
            {
                'name': 'SQlab повнопалі білий', 'category': gloves_cat,
                'price': 1990,
                'description': 'SQlab: біла сітка, логотип на тилу руки, чорний манжет, ергономіка для довгих поїздок.',
                'color': 'Білий/чорний', 'is_featured': True, 'rating': 4.7, 'reviews_count': 46, 'in_stock': True,
                'image_url': '/media/products/gloves/gloves-09.png',
            },
        ]
        gear_items.extend(
            self._extra_gear_batch(
                helmet_cat, clothing_cat, glasses_cat, shoes_cat, gloves_cat, lights_cat
            )
        )

        for g in gear_items:
            g['image_url'] = pick_themed_image(g['category'].slug, g['name'])

        for g in gear_items:
            name = g['name']
            defaults = dict(g)
            defaults.pop('name', None)
            self.upsert_product(name=name, defaults=defaults)

        # Лише два окуляри з локальними фото — прибрати старі демо з БД після повторного сіду
        Product.objects.filter(category__slug='glasses').exclude(
            name__in=('Sport Shield Cyan Mirror', 'VIF Sport Shield Orange Revo')
        ).delete()
        _kept_helmets = (
            'Kask Protone білий матовий',
            'MET Rivale білий глянець',
            'Urban Bowl шолом білий',
            'Aero Silver шолом',
            'MTB Trail помаранчевий з козирком',
            'MET Manta білий/чорний',
            'Silverbird вентильований шолом',
            'Шолом шосейний MIPS білий',
            'Шолом шосейний MIPS профіль',
            'HJC Ibex білий шосейний',
        )
        Product.objects.filter(category__slug='helmet').exclude(name__in=_kept_helmets).delete()
        _kept_gloves = (
            'SKMT Mesh безпалі рукавиці',
            'GripGrab повнопалі сітка',
            'Leatt 1.0 GripR MTB',
            'Leatt 4.0 Lite долоня NanoGrip',
            'Leatt 4.0 Lite білий/чорний',
            'Cognative MTB Marble',
            'Leatt Mesh верх руки',
            'Leatt 4.0 Lite чорний сірий',
            'SQlab повнопалі білий',
        )
        Product.objects.filter(category__slug='gloves').exclude(name__in=_kept_gloves).delete()
        _kept_clothing = (
            'SYN Global білі бібшорти',
            'Resting Cycling Face комплект',
            'SYN бібшорти білий профіль',
            'Бібшорти перфорація біло-чорні',
            'Комплект довгий рукав градієнт',
            'Team Sky Castelli комплект',
            'SYN Global білі з акцентами',
        )
        Product.objects.filter(category__slug='clothing').exclude(name__in=_kept_clothing).delete()
        _kept_shoes = (
            'Shimano S-PHYRE XC білі',
            'Sunlest шосейні білий/чорний',
            'Santic шосейні пара білий/червоний',
            'Santic Atop білий візерунок',
            'Mavic Cosmic SLR білий/сірий',
            'Northwave шосейні білі SLW3',
            'GAERNE шосейні білі BOA',
            "fi'zi:k шосейні біло-сині з лаймом",
            "fi'zi:k шосейні BOA профіль",
        )
        Product.objects.filter(category__slug='shoes').exclude(name__in=_kept_shoes).delete()
        _kept_lights = (
            'Kensington хром передній ретро',
            'PLAZMA задній LED вертикальний',
            'BUCKLOS круглий передній COB',
            'BUCKLOS кіт передній і задній',
            'ROCKBROS передній круглий USB-C',
            'ROCKBROS задній з ременем USB-C',
            'ROCKBROS задній COB круглий',
            'Набір LED перед+зад водостійкий',
            'Smiling Shark подвійний LED дисплей',
            'Smiling Shark передній дисплей профіль',
            'VICTGOAL набір на кермі',
        )
        Product.objects.filter(category__slug='lights').exclude(name__in=_kept_lights).delete()
        _kept_bags = (
            'Cyclite підсідельна bikepacking сіра',
            'Cyclite сумка в раму біла',
            'Cyclite frame pack сітка рефлектор',
            'ROCKBROS барна олива на кермі',
            'LEAD OUT барна біла burrito',
            'Барна сумка чорна на руль',
            'Барна біла ripstop bungee',
            'Барна чорна з сіткою',
            'Alpkit барна roll-top сіра',
        )
        Product.objects.filter(category__slug='bags').exclude(name__in=_kept_bags).delete()

    def _extra_gear_batch(self, helmet_cat, clothing_cat, glasses_cat, shoes_cat, gloves_cat, lights_cat):
        """По 15 демо-товарів у шоломи, вело-форму, окуляри, туфлі, рукавички, ліхтарі."""
        out = []

        def row(name, cat, price, desc, seed, color='Чорний', **extra):
            w = extra.pop('weight', None)
            d = {
                'name': name,
                'category': cat,
                'price': price,
                'description': desc,
                'color': color,
                'is_featured': extra.get('is_featured', False),
                'rating': extra.get('rating', 4.5),
                'reviews_count': extra.get('reviews_count', 48),
                'in_stock': True,
                'image_url': pick_themed_image(cat.slug, name),
            }
            if w is not None:
                d['weight'] = w
            if 'old_price' in extra:
                d['old_price'] = extra['old_price']
            return d

        helmets = []
        for n, p, d, s in helmets:
            out.append(row(n, helmet_cat, p, d, s, color='Різні', rating=4.4 + (len(out) % 5) * 0.1, reviews_count=30 + len(out)))

        clothing = []
        for n, p, d, s in clothing:
            out.append(row(n, clothing_cat, p, d, s, color='Різні', rating=4.5 + (len(out) % 4) * 0.08, reviews_count=40 + len(out) % 80))

        glasses = []
        for n, p, d, s in glasses:
            out.append(row(n, glasses_cat, p, d, s, color='Різні', rating=4.6 + (len(out) % 3) * 0.1, reviews_count=55 + len(out) % 120))

        shoes = []
        for n, p, d, s in shoes:
            out.append(row(n, shoes_cat, p, d, s, color='Різні', rating=4.5 + (len(out) % 6) * 0.07, reviews_count=22 + len(out) % 90))

        gloves = []
        for n, p, d, s in gloves:
            out.append(row(n, gloves_cat, p, d, s, color='Різні', rating=4.4 + (len(out) % 5) * 0.1, reviews_count=60 + len(out) % 200))

        lights = []
        for n, p, d, s in lights:
            out.append(row(n, lights_cat, p, d, s, color='Різні', rating=4.5 + (len(out) % 4) * 0.08, reviews_count=40 + len(out) % 150))

        return out

    def create_stores(self):
        stores = [
            {
                'name': 'Velo-Grad',
                'website': 'https://velo-grad.ua',
                'city': 'Київ',
                'phone': '+380 44 123-45-67',
                'address': 'вул. Хрещатик, 10',
                'description': 'Найбільший велосипедний магазин Києва. Trek, Giant, Merida.',
                'is_online': True,
                'latitude': 50.44710,
                'longitude': 30.52210,
            },
            {
                'name': 'Winkel Sport',
                'website': 'https://winkel.com.ua',
                'city': 'Київ',
                'phone': '+380 44 234-56-78',
                'address': 'пр. Перемоги, 50',
                'description': 'Мережа спортивних магазинів. Широкий асортимент екіпірування.',
                'is_online': True,
                'latitude': 50.45090,
                'longitude': 30.45730,
            },
            {
                'name': 'Velopark',
                'website': 'https://velopark.com.ua',
                'city': 'Львів',
                'phone': '+380 32 345-67-89',
                'address': 'пр. Свободи, 15',
                'description': 'Спеціалізований велосипедний магазин у Львові.',
                'is_online': False,
                'latitude': 49.84160,
                'longitude': 24.03160,
            },
        ]
        for s in stores:
            obj, created = Store.objects.get_or_create(name=s['name'], defaults=s)
            if created:
                continue
            changed = False
            for k, v in s.items():
                if v in (None, ''):
                    continue
                cur = getattr(obj, k, None)
                if cur in (None, ''):
                    setattr(obj, k, v)
                    changed = True
            if changed:
                obj.save()

    def create_store_locations(self):
        stores = {s.name: s for s in Store.objects.all()}

        locations = [
            {
                'store': stores.get('Velo-Grad'),
                'title': 'Velo-Grad (Центр)',
                'city': 'Київ',
                'address': 'вул. Хрещатик, 10',
                'latitude': 50.44710,
                'longitude': 30.52210,
            },
            {
                'store': stores.get('Velo-Grad'),
                'title': 'Velo-Grad (Поділ)',
                'city': 'Київ',
                'address': 'Поділ (пункт видачі)',
                'latitude': 50.46690,
                'longitude': 30.51650,
            },
            {
                'store': stores.get('Velo-Grad'),
                'title': 'Velo-Grad (Дніпро)',
                'city': 'Дніпро',
                'address': 'Центр (пункт видачі)',
                'latitude': 48.46470,
                'longitude': 35.04620,
            },
            {
                'store': stores.get('Winkel Sport'),
                'title': 'Winkel Sport (Київ)',
                'city': 'Київ',
                'address': 'пр. Перемоги, 50',
                'latitude': 50.45090,
                'longitude': 30.45730,
            },
            {
                'store': stores.get('Winkel Sport'),
                'title': 'Winkel Sport (Одеса)',
                'city': 'Одеса',
                'address': 'Центр (пункт видачі)',
                'latitude': 46.48250,
                'longitude': 30.72330,
            },
            {
                'store': stores.get('Velopark'),
                'title': 'Velopark (Львів)',
                'city': 'Львів',
                'address': 'пр. Свободи, 15',
                'latitude': 49.84160,
                'longitude': 24.03160,
            },
            {
                'store': stores.get('Velopark'),
                'title': 'Velopark (Івано‑Франківськ)',
                'city': 'Івано‑Франківськ',
                'address': 'Центр (пункт видачі)',
                'latitude': 48.92260,
                'longitude': 24.71110,
            },
        ]

        for loc in locations:
            store = loc.get('store')
            if not store:
                continue
            StoreLocation.objects.update_or_create(
                store=store,
                latitude=loc['latitude'],
                longitude=loc['longitude'],
                defaults={
                    'title': loc.get('title', ''),
                    'city': loc.get('city', ''),
                    'address': loc.get('address', ''),
                },
            )

    def create_trails(self):
        _Q = 'ixlib=rb-4.0.3&auto=format&fit=crop&w=1400&q=82'
        _B = 'https://images.unsplash.com'
        trails = [
            {
                'name': 'Карпатська кільцева', 'city': 'Буковель',
                'description': 'Легендарна гірська траса через Карпатські хребти. Неймовірні краєвиди, технічні ділянки.',
                'difficulty': 'hard', 'trail_type': 'mtb',
                'distance_km': 45.5, 'elevation_m': 1800, 'duration_hours': 5.5,
                'rating': 4.9,
                'image_url': f'{_B}/photo-1464822759023-fed622ff2c3b?{_Q}',
            },
            {
                'name': 'Київська набережна', 'city': 'Київ',
                'description': 'Легка прогулянкова траса вздовж Дніпра. Ідеально для родин та початківців.',
                'difficulty': 'easy', 'trail_type': 'city',
                'distance_km': 22.0, 'elevation_m': 50, 'duration_hours': 1.5,
                'rating': 4.6,
                'image_url': f'{_B}/photo-1476514525535-07fb3b4ae5f1?{_Q}',
            },
            {
                'name': 'Знесіння — Личаківський ліс', 'city': 'Львів',
                'description': 'Живописний маршрут через парки Львова. Природа, старовинні алеї, помірний рельєф.',
                'difficulty': 'medium', 'trail_type': 'mixed',
                'distance_km': 18.0, 'elevation_m': 320, 'duration_hours': 2.5,
                'rating': 4.7,
                'image_url': f'{_B}/photo-1441974231531-c6227db76b6e?{_Q}',
            },
            {
                'name': 'Одеська морська', 'city': 'Одеса',
                'description': 'Траса вздовж узбережжя Чорного моря. Пляжі, порт, приморський бульвар.',
                'difficulty': 'easy', 'trail_type': 'city',
                'distance_km': 28.0, 'elevation_m': 80, 'duration_hours': 2.0,
                'rating': 4.5,
                'image_url': f'{_B}/photo-1507525428034-b723cf961d3e?{_Q}',
            },
            {
                'name': 'Гуцульське кільце XC', 'city': 'Яремче',
                'description': 'Технічна XC-траса для досвідчених вершників. Корені, камені, переправи.',
                'difficulty': 'extreme', 'trail_type': 'mtb',
                'distance_km': 32.0, 'elevation_m': 2200, 'duration_hours': 6.0,
                'rating': 4.8,
                'image_url': f'{_B}/photo-1519331379826-f10be5486c6f?{_Q}',
            },
            {
                'name': 'Харківський веломаршрут', 'city': 'Харків',
                'description': 'Міський веломаршрут через парки та проспекти Харкова.',
                'difficulty': 'easy', 'trail_type': 'city',
                'distance_km': 25.0, 'elevation_m': 60, 'duration_hours': 1.8,
                'rating': 4.3,
                'image_url': f'{_B}/photo-1500530855697-b586d89ba3ee?{_Q}',
            },
        ]
        for t in trails:
            defaults = {k: v for k, v in t.items() if k not in ('name', 'city')}
            Trail.objects.update_or_create(
                name=t['name'],
                city=t['city'],
                defaults=defaults,
            )
