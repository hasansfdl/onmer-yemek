Onmer Stok & Finans — Bağımsız Masaüstü Uygulaması
==================================================

Özellikler
----------
- Stok takibi (ürün, giriş, çıkış, satış, düzeltme)
- Gelir / gider kayıtları
- Ciro, maliyet, kar/zarar özeti
- Yerel SQLite veritabanı
  - Geliştirme: data/onmer_stok.db (proje klasöründe)
  - Exe: %LOCALAPPDATA%\OnmerStokFinans\onmer_stok.db (güncellemede korunur)
- Web sitesiyle HİÇBİR bağlantı yok

Geliştirme modunda çalıştırma
------------------------------
    pip install -r onmer_stok_desktop/requirements.txt
    python -m onmer_stok_desktop.main

Windows .exe derleme
--------------------
    .\packaging\build_stok_windows.ps1

Çıktı klasörü:
    dist\OnmerStokFinans\
        OnmerStokFinans.exe
        OKU_BENI.txt

Veritabanı exe klasöründe değil; Windows kullanıcı veri klasöründe tutulur.
Başka bilgisayara taşımak için exe klasörünü ve
%LOCALAPPDATA%\OnmerStokFinans klasörünü birlikte kopyalayın.
