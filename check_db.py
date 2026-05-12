import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from velos.bikes.models import Product, Category, Brand, Store, Trail

products = Product.objects.all()
print(f"Products: {products.count()}")
for p in products[:5]:
    print(f" - {p.name}: image={bool(p.image)}, image_url={p.image_url}")

categories = Category.objects.all()
print(f"Categories: {categories.count()}")
for c in categories[:5]:
    print(f" - {c.name}: icon={c.icon}")

brands = Brand.objects.all()
print(f"Brands: {brands.count()}")
for b in brands[:5]:
    print(f" - {b.name}: logo={bool(b.logo)}")
    
stores = Store.objects.all()
print(f"Stores: {stores.count()}")

trails = Trail.objects.all()
print(f"Trails: {trails.count()}")
for t in trails[:5]:
    print(f" - {t.name}: image_url={t.image_url}")
