import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from velos.bikes.models import Product, ProductImage

bike_images = [
    '/media/products/specialized-rockhopper-expert.jpg',
    '/media/products/trek-domane-al-3.jpg',
    '/media/products/trek-marlin-7-gen-2.jpg',
    '/media/products/giant-liv-avail-ar-4.jpg',
    '/media/products/giant-trance-x-29-2.jpg',
    '/media/products/merida-bignine-300.jpg',
    '/media/products/haibike-sduro-hardnine-50.jpg',
    '/media/products/cube-reaction-hybrid-pro-500.jpg',
    '/media/products/merida-crossway-40-lady.jpg',
    '/media/products/trek-fx-3-disc-womens.jpg',
]

bikes = list(Product.objects.filter(category__name__icontains='велосипед'))
for i, b in enumerate(bikes):
    img_url = bike_images[i % len(bike_images)]
    b.image_url = img_url
    b.save()
    
    ProductImage.objects.filter(product=b).delete()
    ProductImage.objects.create(product=b, image_url=img_url)
    print(f"Fixed image for {b.name} -> {img_url}")

