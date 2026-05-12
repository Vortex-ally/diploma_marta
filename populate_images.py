import os
import django
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import json
from io import BytesIO
from PIL import Image

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from bikes.models import Product, Trail
from django.core.files.base import ContentFile
from django.conf import settings

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
            # image is wider than target, crop width
            new_width = int(target_ratio * img.height)
            offset = (img.width - new_width) // 2
            img = img.crop((offset, 0, offset + new_width, img.height))
        elif img_ratio < target_ratio:
            # image is taller than target, crop height
            new_height = int(img.width / target_ratio)
            offset = (img.height - new_height) // 2
            img = img.crop((0, offset, img.width, offset + new_height))
            
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def get_image_url(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    print(f"Searching for: {query}")
    # Try DuckDuckGo
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query + ' filetype:jpg')}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', class_='result__url'):
            href = a.get('href', '')
            if href.endswith('.jpg') or href.endswith('.png'):
                return href
    except Exception as e:
        pass

    # Try Bing as fallback
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', class_='iusc'):
            m = a.get('m')
            if m:
                data = json.loads(m)
                if 'murl' in data:
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

def update_products():
    for p in Product.objects.all():
        print(f"Processing product: {p.name}")
        cat_name = p.category.name.lower()
        if 'велосипед' in cat_name:
            query = f"{p.name} bicycle"
        else:
            query = f"{p.name} cycling gear"
            
        url = get_image_url(query)
        if url:
            img_data = process_image(url)
            if img_data:
                filename = f"{p.slug}.jpg"
                p.image.save(filename, ContentFile(img_data), save=True)
                p.image_url = ''
                p.save()
                print(f"Successfully saved image for {p.name}")
            else:
                print(f"Failed to process image data for {p.name}")
        else:
            print(f"Found no image url for {p.name}")
        time.sleep(1)

def update_trails():
    media_trails_dir = os.path.join(settings.MEDIA_ROOT, 'trails')
    os.makedirs(media_trails_dir, exist_ok=True)
    
    for t in Trail.objects.all():
        print(f"Processing trail: {t.name}")
        query = f"{t.name} trail {t.city}"
        url = get_image_url(query)
        if url:
            img_data = process_image(url)
            if img_data:
                filename = f"trail_{t.id}.jpg"
                filepath = os.path.join(media_trails_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                t.image_url = f"/media/trails/{filename}"
                t.save()
                print(f"Successfully saved image for {t.name}")
            else:
                print(f"Failed to process image data for {t.name}")
        else:
            print(f"Found no image url for {t.name}")
        time.sleep(1)

if __name__ == "__main__":
    print("Updating products...")
    update_products()
    print("Updating trails...")
    update_trails()
    print("Done!")
