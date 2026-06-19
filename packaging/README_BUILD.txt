Onmer Admin Panel — Windows kurulum paketi
==========================================

1) Geliştirici makinede paket oluşturma
---------------------------------------
PowerShell (yönetici gerekmez):

    cd <proje_kökü>\onmer_yemekcilik
    .\packaging\build_windows.ps1

Çıktı: dist\OnmerAdminPanel\ klasörü
  - OnmerAdminPanel.exe
  - _internal\  (Python + kütüphaneler)
  - manage.py, onmer\, core\, menu\, …, templates\, static\
  - İsteğe bağlı: db.sqlite3 (betik geliştirme klasörünüzde varsa kopyalar)

Bu klasörü USB ile başka bilgisayara kopyalayıp OnmerAdminPanel.exe çalıştırabilirsiniz.


2) Kurulum sihirbazı (.exe setup)
---------------------------------
Inno Setup 6 yükleyin: https://jrsoftware.org/isdl.php

Önce build_windows.ps1 çalıştırıldıktan sonra:

    ISCC.exe packaging\OnmerAdminSetup.iss

Çıktı: dist\OnmerAdminPanel_Setup_1.0.0.exe


3) Veritabanı
-------------
Django varsayılanı: PostgreSQL (POSTGRES_* ortam değişkenleri, bkz. onmer/settings.py).

Taşınabilir SQLite için USE_SQLITE=1 verin; bu durumda veritabanı dosyası Windows'ta
  %LOCALAPPDATA%\Onmer\AdminPanel\db.sqlite3
altına yazılır (Program Files altında değil).

Kurulu .exe (Inno) ile PostgreSQL kullanımı — Kolay yol:
  A) OnmerAdminPanel.exe ile aynı klasöre "onmer_database.env" dosyası koyun.
     packaging\onmer_database.env.example dosyasını şablon alın; adını onmer_database.env yapın.
  B) Veya Windows kullanıcı/sistem ortam değişkenlerinde POSTGRES_HOST, POSTGRES_DB, … tanımlayın.

Not: .env dosyası Program Files altına yazmak için yönetici izni gerekebilir; alternatif olarak
sistem ortam değişkenleri veya kullanıcı düzeyi değişkenler kullanın.

manage.py ile createsuperuser / migrate: Kurulum klasöründe OnmerAdminPanel.exe varken
aynı SQLite yolu (AppData) kullanılır; PostgreSQL'de doğrudan sunucuya bağlanırsınız.


4) Sorun giderme
----------------
- “Veritabanına bağlanılamadı”: db.sqlite3 eksik / bozuk veya PostgreSQL ayarları hatalı.
- Logo görünmez: static\images\onmer-logo-transparent.png kurulum klasöründe olmalı (betik static\’i kopyalar).
