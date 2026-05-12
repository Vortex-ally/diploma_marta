import os
import django
import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
import time
from io import BytesIO
from PIL import Image

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from bikes.models import Product
from django.core.files.base import ContentFile
TARGET_SIZE = (800, 600)

def crop_and_resize(img_data):
    try:
        img = Image.open(BytesIO(img_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # calculate target aspect ratio
        target_ratio = TARGET_SIZE[0] / TARGET_SIZE[1]
        img_ratio = img.width / img.height
        
        if img_ratio > target_ratio:
            new_width = int(target_ratio * img.height)
            offset = (img.width - new_width) // 2
            img = img.crop((offset, 0, offset + new_width, img.height))
        elif img_ratio < target_ratio:
            new_height = int(img.width / target_ratio)
            offset = (img.height - new_height) // 2
            img = img.crop((0, offset, img.width, offset + new_height))
            
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        img.save(output, format='JPEG', quality=90)
        return output.getvalue()
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def fetch_image(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', class_='result__url'):
            href = a.get('href', '')
            if href.endswith('.jpg'):
                return href
    except Exception as e:
        pass

    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.find_all('a', class_='iusc'):
            m = a.get('m')
            if m:
                data = json.loads(m)
                if 'murl' in data and data['murl'].endswith('.jpg'):
                    return data['murl']
    except Exception as e:
        pass
    return None

def process_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return crop_and_resize(r.content)
    except Exception as e:
        print(f"Failed to process {url} - {e}")
    return None

bikes_to_fix = [
    "Cannondale Adventure Neo 3",
    "Specialized Turbo Vado 4.0",
    "Trek Powerfly 5 Gen 4",
    "Cube Reaction Hybrid Pro 500",
    "Author Matrix 20"
]

print("Starting custom image update...")
for name in bikes_to_fix:
    print(f"Fixing {name}...")
    try:
        p = Product.objects.get(name__icontains=name)
        # Add 'white background jpg' to force solid background
        query = f"{name} bicycle white background studio .jpg"
        url = fetch_image(query)
        if url:
            print(f"   Found URL: {url}")
            img_data = process_image(url)
            if img_data:
                filename = f"{p.slug}-fixed.jpg"
                p.image.save(filename, ContentFile(img_data), save=True)
                p.image_url = ''
                p.save()
                print(f"   Successfully saved new image for {name}")
            else:
                print(f"   Failed to process image data for {name}")
        else:
            print(f"   Found no image url for {name}")
    except Product.DoesNotExist:
        print(f"   Product {name} not found in DB")
    time.sleep(2)

print("Done.")
