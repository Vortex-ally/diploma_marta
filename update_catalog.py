import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from bikes.models import Product, Category, Trail, ProductImage
import random

# TASK 1: Fix Scott Addict RC Team Issue color
scott_team = Product.objects.filter(name__icontains='Scott Addict RC Team Issue').first()
if scott_team:
    scott_team.color = 'Перлинно-бузковий'
    scott_team.save()
    print("Fixed color for Scott Addict RC Team Issue")

# TASK 2: Filter Новинки
Product.objects.all().update(is_new=False)
# Select some specific cool products to be "New"
new_bike_names = [
    'Scott Addict RC Pro AXS',
    'Cannondale SuperSix EVO LAB71',
    'Factor O2 VAM Ultegra Di2',
    'Canyon Ultimate CF SLX',
]
Product.objects.filter(name__in=new_bike_names).update(is_new=True)

# Also make some top-tier gear new
gear_cat = Category.objects.filter(slug='bags').first()
if gear_cat:
    bags = Product.objects.filter(category=gear_cat)[:2]
    for b in bags:
        b.is_new = True
        b.save()

print(f"Set {Product.objects.filter(is_new=True).count()} items as New.")

# TASK 3 & 4: Professional Descriptions & White Background Images
bike_data = {
    'Canyon Ultimate CF SL 8': {
        'desc': '''Легендарний шосейний велосипед з ідеальним балансом ваги, жорсткості та аеродинаміки. Карбонова рама преміум-класу забезпечує виняткову передачу потужності.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Карбонова рама CF SL
- Трансмісія Shimano Ultegra 11 швидкостей
- Колеса DT Swiss
- Аеродинамічний кокпіт Canyon''',
        'url': 'https://s3.amazonaws.com/www.bikerumor.com/wp-content/uploads/2022/09/08125026/Canyon-Ultimate-CF-SLX-8-Di2-1-1068x601.jpg'
    },
    'Scott Addict RC Pro AXS': {
        'desc': '''Топовий гоночний шосейник від Scott. Найлегша карбонова рама HMX, повністю інтегрована проводка та електронне перемикання передач від SRAM для максимальної продуктивності на підйомах.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Карбонова рама HMX
- Бездротова трансмісія SRAM RED eTap AXS 12-speed
- Карбонові колеса Zipp 303 Firecrest
- Повна інтеграція кабелів''',
        'url': 'https://media.scott-sports.com/q_auto,w_1000,f_auto,dpr_1.0/image/upload/qsyl6eokj68mxy5lgh0o'
    },
    'Scott Addict RC Team Issue': {
        'desc': '''Елітний шосейний велосипед, створений для професійних гонщиків команди Team DSM. Надзвичайно легкий і жорсткий, ідеальний для гірських етапів.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Карбонова рама HMX-SL (найлегша в лінійці)
- Електронна трансмісія Shimano Dura-Ace Di2 12-speed
- Колеса Syncros Capital 1.0 35 Disc
- Вага всього 6.95 кг''',
        'url': 'https://media.scott-sports.com/q_auto,w_1000,f_auto,dpr_1.0/image/upload/rt5aedg9c6h2f2v2t4q1'
    },
    'Cannondale SuperSix EVO LAB71': {
        'desc': '''Вершина інженерної думки Cannondale. Серія LAB71 використовує найкращий карбон Series 0 для створення найшвидшого і найлегшого SuperSix EVO в історії.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Надлегка рама LAB71 Edition Series 0 Carbon
- Трансмісія Shimano Dura-Ace Di2
- Колеса HollowGram R-SL 50 Carbon
- Аеродинамічний інтегрований руль''',
        'url': 'https://media.cannondale.com/media/catalog/product/c/2/c21102u_supersix_evo_lab71_mbl_pd_1_1.jpg'
    },
    'Factor O2 VAM Ultegra Di2': {
        'desc': '''Ультралегкий велосипед, створений для підкорення найкрутіших перевалів. VAM означає "Velocita Ascensionale Media" - середня швидкість підйому.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Рама O2 VAM з карбону TeXtreme, Toray, Nippon Graphite
- Трансмісія Shimano Ultegra Di2 12-speed
- Карбонові колеса Black Inc Twenty
- Керамічні підшипники CeramicSpeed''',
        'url': 'https://factorbikes.com/wp-content/uploads/2023/07/Factor-O2-VAM-Red-Velvet-Black-Inc-Wheels-1-1024x576.jpg'
    },
    'Scott Addict RC SRAM Red AXS': {
        'desc': '''Преміальна версія Scott Addict RC з топовою бездротовою групою SRAM Red. Максимальна ефективність та неперевершений вигляд.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Карбонова рама HMX
- SRAM RED eTap AXS 12 швидкостей
- Колеса Syncros Capital 1.0 35
- Інтегрований карбоновий кокпіт Creston iC SL''',
        'url': 'https://media.scott-sports.com/q_auto,w_1000,f_auto,dpr_1.0/image/upload/rt5aedg9c6h2f2v2t4q1'
    },
    'Canyon Ultimate CF SLX': {
        'desc': '''Професійний рівень шосейного велосипеда від Canyon. Рама CF SLX забезпечує ідеальний баланс між надлегкою вагою та високою жорсткістю для спринтів.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Карбонова рама CF SLX
- Трансмісія Shimano Dura-Ace
- Карбонові аеродинамічні колеса
- Паверметр у комплекті''',
        'url': 'https://s3.amazonaws.com/www.bikerumor.com/wp-content/uploads/2022/09/08125026/Canyon-Ultimate-CF-SLX-8-Di2-1-1068x601.jpg'
    },
    'Merida Scultura 400': {
        'desc': '''Ідеальний шосейний велосипед для початківців та любителів. Легка алюмінієва рама з карбоновою вилкою забезпечує комфорт і швидкість на асфальті.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Легка алюмінієва рама Scultura Lite BSA
- Повністю карбонова вилка Scultura CF
- Надійна трансмісія Shimano 105 11 швидкостей
- Гідравлічні дискові гальма''',
        'url': 'https://www.merida-bikes.com/p181/b2b/media/sys_master/images/ha2/hb7/9891820474398.jpg'
    },
    'Scott Addict 30': {
        'desc': '''Ендуранс-шосейник, створений для комфортного подолання великих дистанцій. Геометрія рами орієнтована на витривалість, а не лише на гонки.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Карбонова рама Addict HMF Carbon
- Трансмісія Shimano 105 11 швидкостей
- Колеса Syncros RP2.0 Disc
- Компоненти Syncros з акцентом на комфорт''',
        'url': 'https://media.scott-sports.com/q_auto,w_1000,f_auto,dpr_1.0/image/upload/v1585233157/product-images/280628.jpg'
    },
    'Cannondale Synapse AL 105': {
        'desc': '''Універсальний ендуранс-велосипед з алюмінієвою рамою. Створений для комфорту на неідеальних дорогах завдяки системі мікроамортизації SAVE.

ОСНОВНІ ХАРАКТЕРИСТИКИ:
- Алюмінієва рама SmartForm C2 Alloy, SAVE
- Карбонова вилка
- Трансмісія Shimano 105
- Геометрія Endurance для довгої їзди''',
        'url': 'https://media.cannondale.com/media/catalog/product/c/2/c21102u_supersix_evo_lab71_mbl_pd_1_1.jpg'
    }
}

bikes_cat = Category.objects.filter(name__icontains='велосипед').first()
if bikes_cat:
    bikes = Product.objects.filter(category=bikes_cat)
    for b in bikes:
        if b.name in bike_data:
            b.description = bike_data[b.name]['desc']
            b.image_url = bike_data[b.name]['url']
            b.save()
            
            # Create/update product images
            ProductImage.objects.filter(product=b).delete()
            ProductImage.objects.create(product=b, image_url=bike_data[b.name]['url'])
            
            print(f"Updated description and image for: {b.name}")

# TASK 5: Add new trails
print("Adding new trails...")
Trail.objects.all().delete() # Clean old trails to make fresh
trails_data = [
    {
        'name': 'Київська сотка', 'city': 'Київ', 
        'desc': 'Знаменитий марафонський маршрут навколо Києва. Ідеально підходить для шосейних велосипедів. Дорога переважно з якісним асфальтом, але є невеликі ділянки з бруківкою.',
        'difficulty': 'medium', 'trail_type': 'road', 'dist': 100, 'elev': 700, 'dur': 4.0,
        'lat': 50.4501, 'lng': 30.5234, 'img': 'https://images.unsplash.com/photo-1541625602330-2277a4c46182?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Гравійні ліси Пущі-Водиці', 'city': 'Київ', 
        'desc': 'Прекрасний маршрут для гравійника. Густий ліс, широкі ґрунтові дороги з невеликою кількістю піску. Особливо гарно восени.',
        'difficulty': 'easy', 'trail_type': 'gravel', 'dist': 35, 'elev': 250, 'dur': 2.5,
        'lat': 50.5401, 'lng': 30.3456, 'img': 'https://images.unsplash.com/photo-1533560904424-a0c61dc306fc?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Карпатський перевал', 'city': 'Карпати', 
        'desc': 'Складний гірський маршрут для MTB. Круті підйоми, кам\'янисті спуски та неймовірні краєвиди з вершин. Вимагає гарної фізичної підготовки.',
        'difficulty': 'hard', 'trail_type': 'mtb', 'dist': 45, 'elev': 1200, 'dur': 5.0,
        'lat': 48.4521, 'lng': 24.3214, 'img': 'https://images.unsplash.com/photo-1574620025774-a0212720d2ba?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Львівська бруківка', 'city': 'Львів', 
        'desc': 'Міський маршрут історичним центром Лева. Багато бруківки, вузькі вулички та атмосферні кав\'ярні. Рекомендується міський або гравійний велосипед.',
        'difficulty': 'easy', 'trail_type': 'road', 'dist': 15, 'elev': 150, 'dur': 1.5,
        'lat': 49.8397, 'lng': 24.0297, 'img': 'https://images.unsplash.com/photo-1574620025774-a0212720d2ba?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80' # Placeholder, will use appropriate image if possible
    },
    {
        'name': 'Одеська траса Здоров\'я', 'city': 'Одеса', 
        'desc': 'Найкраще місце для велопрогулянок в Одесі. Асфальтована доріжка вздовж моря без автомобілів. Ідеально для новачків і сімей з дітьми.',
        'difficulty': 'easy', 'trail_type': 'road', 'dist': 12, 'elev': 50, 'dur': 1.0,
        'lat': 46.4825, 'lng': 30.7233, 'img': 'https://images.unsplash.com/photo-1520638541334-a083b02bbfa0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Голосіївський трейл', 'city': 'Київ', 
        'desc': 'Справжній рай для любителів MTB в межах столиці. Безліч стежок, апхілів та даунхілів. Маршрут можна адаптувати під будь-який рівень.',
        'difficulty': 'medium', 'trail_type': 'mtb', 'dist': 25, 'elev': 500, 'dur': 2.0,
        'lat': 50.3800, 'lng': 30.5100, 'img': 'https://images.unsplash.com/photo-1571166687467-33f7ed6fba94?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Синевирський перевал', 'city': 'Карпати', 
        'desc': 'Мальовничий гравійний маршрут до озера Синевир. Фантастичні пейзажі, свіже гірське повітря та помірні підйоми.',
        'difficulty': 'medium', 'trail_type': 'gravel', 'dist': 60, 'elev': 900, 'dur': 6.0,
        'lat': 48.6167, 'lng': 23.6833, 'img': 'https://images.unsplash.com/photo-1498616239103-61a7a242fae3?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Буковель Даунхіл', 'city': 'Карпати', 
        'desc': 'Екстремальний спуск спеціально обладнаними трасами Буковель Байк Парку. Тільки для підготовлених райдерів на двопідвісах.',
        'difficulty': 'hard', 'trail_type': 'mtb', 'dist': 10, 'elev': 50, 'dur': 0.75,
        'lat': 48.3538, 'lng': 24.4128, 'img': 'https://images.unsplash.com/photo-1534145719991-314d101d2ce8?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Ірпінська набережна', 'city': 'Ірпінь', 
        'desc': 'Нова асфальтована велодоріжка вздовж річки Ірпінь. Чудове місце для вечірньої поїздки на шосейному або міському велосипеді.',
        'difficulty': 'easy', 'trail_type': 'road', 'dist': 8, 'elev': 20, 'dur': 0.66,
        'lat': 50.5167, 'lng': 30.2500, 'img': 'https://images.unsplash.com/photo-1541625602330-2277a4c46182?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    },
    {
        'name': 'Дніпровські кручі', 'city': 'Дніпро', 
        'desc': 'Гравійний маршрут вздовж правого берега Дніпра. Багато панорамних точок та цікавий рельєф з короткими стрімкими підйомами.',
        'difficulty': 'medium', 'trail_type': 'gravel', 'dist': 40, 'elev': 400, 'dur': 3.5,
        'lat': 48.4647, 'lng': 35.0461, 'img': 'https://images.unsplash.com/photo-1533560904424-a0c61dc306fc?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80'
    }
]

for t in trails_data:
    Trail.objects.create(
        name=t['name'],
        city=t['city'],
        description=t['desc'],
        difficulty=t['difficulty'],
        trail_type=t['trail_type'],
        distance_km=t['dist'],
        elevation_m=t['elev'],
        duration_hours=t['dur'],
        latitude=t['lat'],
        longitude=t['lng'],
        image_url=t['img']
    )
print(f"Created {len(trails_data)} trails.")
