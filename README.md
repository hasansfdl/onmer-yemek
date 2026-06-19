# Onmer Yemek Organizasyon

Premium catering & toplu yemek firması için modern, responsive Django 6 web sitesi.
Bootstrap 5 + altın/siyah tonlarda kurumsal tasarım, online sipariş sistemi,
takvim destekli randevu ve admin panelinden tam içerik kontrolü içerir.

## Özellikler

- **Ana sayfa** — Hero alanı, hizmet kartları, animasyonlu istatistikler, öne çıkan yemekler ve galeri özeti.
- **Hakkımızda** — Misyon, vizyon, başarı istatistikleri.
- **Yemekler & Menü** — Kategori filtreleme, kart yapısı, kalori/içerik bilgisi, haftalık menü tablosu.
- **Online Toplu Sipariş** — Kişi sayısı, tarih, organizasyon türü ve özel notlarla form. Veritabanına kaydedilir.
- **Randevu Sistemi** — Takvim destekli tarih/saat seçimi, AJAX uygunluk kontrolü, çift rezervasyon engeli.
- **Galeri / Portfolyo** — Masonry grid, GLightbox lightbox sistemi, kategori filtresi.
- **Lokasyon & Lojistik** — Google Maps embed, hizmet bölgeleri, araç filosu.
- **İletişim** — Form, telefon, WhatsApp, sosyal medya.
- **Hesap Sistemi** — Kayıt, giriş, çıkış (Django Auth).
- **Admin Paneli** — Tüm modeller için zengin admin (önizleme, inline form, filter, search, list_editable).
- **Tasarım** — Siyah / koyu gri / altın paleti, Playfair Display + Poppins fontları, AOS animasyonları, smooth scroll, sayfa yükleme animasyonu, floating WhatsApp butonu, toast bildirimler.

## Klasör Yapısı

```
onmer_yemekcilik/
├── manage.py
├── requirements.txt
├── db.sqlite3                # migrate sonrası oluşur
├── onmer/                    # Ana proje (settings, urls, wsgi)
├── core/                     # Site geneli (home, about, contact, services)
├── accounts/                 # Kayıt / Giriş
├── menu/                     # Yemek katalogu + haftalık menü
├── orders/                   # Toplu sipariş sistemi
├── reservations/             # Takvim destekli randevu
├── portfolio/                # Galeri / portfolyo
├── templates/                # Proje genel template'leri
├── static/                   # CSS, JS
└── media/                    # Kullanıcı yüklemeleri (yemek/galeri görselleri)
```

## Hızlı Kurulum

```powershell
# 1. Bağımlılıkları kur
python -m pip install -r requirements.txt

# 2. Migration'ları oluştur ve uygula
python manage.py makemigrations
python manage.py migrate

# 3. Süper kullanıcı oluştur
python manage.py createsuperuser

# 4. Örnek veri yükle (opsiyonel)
python manage.py seed_demo

# 5. Sunucuyu başlat
python manage.py runserver
```

Site: http://127.0.0.1:8000/  ·  Admin: http://127.0.0.1:8000/admin/

## Renk Paleti

| Token | Hex |
|--|--|
| Black | `#0b0b0d` |
| Card | `#15151a` |
| Border | `#2a2a32` |
| Gold | `#d4af37` |
| Gold Light | `#f4d06f` |
| Gold Deep | `#a8841d` |

## E-posta (İletişim Formu ve Sipariş Bildirimi)

İletişim formundan gönderilen mesajlar ile **sipariş ödemesi onaylandığında**
gönderilen bilgilendirme mailleri, aynı SMTP ayarını kullanır. Alıcı adresi
**Admin → Site Ayarları → E-posta** alanındaki kayıttır. *Reply-To* başlığı
iletişim formunda doğrudan müşteriye, siparişte müşterinin sipariş e-postasına
işaret eder.

Varsayılan kurulumda `console` backend aktiftir — mesaj sadece runserver
terminaline yazılır. Gerçek inbox'a düşmesi için aşağıdaki adımları izle:

### Gmail App Password ile (önerilen)

1. Gmail hesabında **2-Step Verification** açık olmalı:
   <https://myaccount.google.com/security>
2. **App passwords**: <https://myaccount.google.com/apppasswords>
   → "Onmer Site" gibi bir ad ile yeni şifre oluştur (16 haneli kod).
3. Sunucuyu başlatmadan ÖNCE şu ortam değişkenlerini tanımla:

```powershell
$env:EMAIL_HOST_USER="hasansafdel9931@gmail.com"
$env:EMAIL_HOST_PASSWORD="xxxx xxxx xxxx xxxx"   # 16 haneli App Password
python manage.py runserver
```

Bu kadar — formdan veya sipariş tamamlandığında gönderilen her mesaj artık
`Site Ayarları → E-posta` alanındaki adrese gerçek mail olarak gelir. Test için
`/iletisim/` sayfasından bir mesaj veya tamamlanmış bir toplu sipariş akışı
kullanın.

### Kalıcı yapmak (her seferinde yazmamak için)

PowerShell kullanıcı profilini düzenle: `notepad $PROFILE` ve şu satırları ekle:

```powershell
$env:EMAIL_HOST_USER="hasansafdel9931@gmail.com"
$env:EMAIL_HOST_PASSWORD="xxxx xxxx xxxx xxxx"
```

### Farklı SMTP servisleri

Yandex, Outlook, Mailgun, SendGrid vs. için ek değişkenler:

```powershell
$env:EMAIL_HOST="smtp.yandex.com"     # default: smtp.gmail.com
$env:EMAIL_PORT="465"                 # default: 587
$env:EMAIL_USE_TLS="0"
$env:EMAIL_USE_SSL="1"
```

## Üretime Hazırlık

`onmer/settings.py` içinde:

- `DEBUG = False`
- `ALLOWED_HOSTS = ['ornek.com.tr']`
- `SECRET_KEY` ortam değişkeninden okunsun
- `STATIC_ROOT` için `python manage.py collectstatic` çalıştırın
- E-posta için yukarıdaki SMTP ortam değişkenlerini tanımlayın

## Lisans

Tüm hakları Onmer Yemek Organizasyon firmasına aittir.
