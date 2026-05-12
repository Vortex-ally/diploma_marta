import os, django, urllib.request, ssl

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from velos.bikes.models import Product, Trail, ProductImage

# Disable SSL verification for simple downloads
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 1. Download Bike Images
bike_media_dir = '/Users/marta/Desktop/duplom /media/products/bikes'
os.makedirs(bike_media_dir, exist_ok=True)

bikes = Product.objects.filter(category__name__icontains='велосипед')
for b in bikes:
    if b.image_url and b.image_url.startswith('http'):
        filename = f"bike_{b.id}.jpg"
        filepath = os.path.join(bike_media_dir, filename)
        try:
            req = urllib.request.Request(b.image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            
            local_url = f"/media/products/bikes/{filename}"
            b.image_url = local_url
            b.save()
            
            ProductImage.objects.filter(product=b).delete()
            ProductImage.objects.create(product=b, image_url=local_url)
            print(f"Downloaded image for bike {b.name}")
        except Exception as e:
            print(f"Failed to download bike image {b.image_url}: {e}")

# 2. Download Trail Images
trail_media_dir = '/Users/marta/Desktop/duplom /media/trails'
os.makedirs(trail_media_dir, exist_ok=True)

trails = Trail.objects.all()
for t in trails:
    if t.image_url and t.image_url.startswith('http'):
        filename = f"trail_{t.id}.jpg"
        filepath = os.path.join(trail_media_dir, filename)
        try:
            req = urllib.request.Request(t.image_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx) as response, open(filepath, 'wb') as out_file:
                out_file.write(response.read())
            
            local_url = f"/media/trails/{filename}"
            t.image_url = local_url
            t.save()
            print(f"Downloaded image for trail {t.name}")
        except Exception as e:
            print(f"Failed to download trail image {t.image_url}: {e}")

print("Done downloading images!")
