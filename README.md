# miracotoelektronik - Local demo

Bu repository’ye basit bir Flask uygulaması eklenmiştir: kullanıcı girişi, marka/anahtar yönetimi ve anahtar fiyat takibi.

- Başlatma:
  - python -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt
  - export FLASK_APP=app.py
  - flask run

Not: Bu demo uygulama basit doğrulama (plain password) kullanır; üretimde şifreleme ve daha güçlü auth gerekir.
