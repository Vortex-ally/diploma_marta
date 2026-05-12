import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from bikes.models import Product, Trail

products_without_images = Product.objects.filter(image_url='').count()
trails_without_images = Trail.objects.filter(image_url='').count()

print(f"Products without images: {products_without_images}")
print(f"Trails without images: {trails_without_images}")

if products_without_images == 0 and trails_without_images == 0:
    print("All products and trails have images!")
else:
    print("Some items still missing images.")
