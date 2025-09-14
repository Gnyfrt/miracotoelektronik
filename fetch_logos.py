import os
import requests

# Marka slugları Simple Icons CDN ile eşleşecek şekilde hazırlanmalı (küçük harf, boşluk->-, bazı karakterler temizlenmeli)
brands = [
  'Renault','Fiat','Ford','Volkswagen','Toyota','Hyundai','Opel','Mercedes-Benz','BMW','Audi',
  'Honda','Nissan','Peugeot','Citroën','Skoda','Seat','Dacia','Mitsubishi','Kia','Isuzu',
  'Suzuki','Lexus','Porsche','Subaru','Mini','Jaguar','Land Rover','Volvo','Tesla','Alfa Romeo'
]

def slugify(name):
    s = name.lower()
    s = s.replace(' ', '-')
    s = s.replace('ç','c').replace('ğ','g').replace('ü','u').replace('ş','s').replace('ö','o').replace('ı','i')
    s = s.replace('.', '').replace('/', '-')
    return s

OUT_DIR = os.path.join('static', 'logos')
os.makedirs(OUT_DIR, exist_ok=True)

for name in brands:
    slug = slugify(name)
    url = f'https://cdn.simpleicons.org/{slug}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.text.strip().startswith('<svg'):
            path = os.path.join(OUT_DIR, f'{slug}.svg')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(r.text)
            print('Saved', path)
        else:
            print('Not found on CDN:', name, '->', url, 'status', r.status_code)
    except Exception as e:
        print('Error fetching', name, e)