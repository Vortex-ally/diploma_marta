import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from velos.bikes.models import Trail

good_trail_images = [
    '/media/trails/trail_19.jpg',
    '/media/trails/trail_20.jpg',
    '/media/trails/trail_27.jpg',
    '/media/trails/trail_28.jpg',
]

trails = Trail.objects.all()
for i, t in enumerate(trails):
    t.image_url = good_trail_images[i % len(good_trail_images)]
    t.save()
    print(f"Fixed image for {t.name}")

