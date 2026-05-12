import os
import django
import requests
from bs4 import BeautifulSoup
import time
import re
import urllib.parse
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'velosite.settings')
django.setup()

from bikes.models import Product, Category, Brand, Store, Trail

def get_image_url(query):
    # Try searching duckduckgo html
    print(f"Searching for: {query}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query + ' filetype:jpg')}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Sometimes DDG returns external links to images
        for a in soup.find_all('a', class_='result__url'):
            href = a.get('href', '')
            if href.endswith('.jpg') or href.endswith('.png'):
                return href
    except Exception as e:
        print(f"DDG error: {e}")

    # Fallback: Scrape Bing images
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
        print(f"Bing error: {e}")
        
    return None

def update_products():
    for p in Product.objects.all():
        if 'picsum' in p.image_url or not p.image_url:
            query = f"{p.name} bicycle"
            url = get_image_url(query)
            if url:
                print(f"Product {p.name} -> {url}")
                p.image_url = url
                p.save()
            else:
                print(f"Found no image for Product: {p.name}")
            time.sleep(1)

def update_trails():
    for t in Trail.objects.all():
        if not t.image_url or 'picsum' in t.image_url:
            query = f"{t.name} trail {t.city}"
            url = get_image_url(query)
            if url:
                print(f"Trail {t.name} -> {url}")
                t.image_url = url
                t.save()
            else:
                print(f"Found no image for Trail: {t.name}")
            time.sleep(1)

if __name__ == "__main__":
    print("Updating products...")
    update_products()
    print("Updating trails...")
    update_trails()
    print("Done!")
