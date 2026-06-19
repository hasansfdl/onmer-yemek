"""Models shared across the marketing pages of the website.

`SiteSetting` is a soft singleton: only the first row is ever served to the
templates so the admin can edit the brand contact info, hero text and
statistics without touching code.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteSetting(models.Model):
    """Editable brand information shown across the website."""

    company_name = models.CharField(_('Firma Adı'), max_length=120,
                                    default='Onmer Yemek Organizasyon')
    tagline = models.CharField(_('Slogan'), max_length=200,
                               default='Premium Catering & Toplu Yemek Hizmetleri')
    hero_title = models.CharField(_('Hero Başlığı'), max_length=200,
                                  default='Lezzeti Sanata Dönüştürüyoruz')
    hero_subtitle = models.CharField(
        _('Hero Alt Başlık'), max_length=300,
        default='Düğün, nişan, kurumsal organizasyon ve toplu yemek '
                'hizmetlerinde 20+ yıllık deneyim.',
    )

    phone = models.CharField(_('Telefon'), max_length=30,
                             default='+90 555 123 45 67')
    whatsapp = models.CharField(_('WhatsApp Numarası'), max_length=30,
                                default='905551234567',
                                help_text=_('Sadece rakam, başında ülke kodu ile.'))
    email = models.EmailField(_('E-posta'), default='info@onmeryemek.com')
    address = models.CharField(_('Adres'), max_length=255,
                               default='Kadıköy, İstanbul, Türkiye')

    google_maps_embed = models.TextField(
        _('Google Maps URL'),
        blank=True,
        default='https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d96363.07'
                '!2d29.0!3d40.99!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x14cab9b40521e5cd%3A0x0!2zS2FkxLFrw7Z5!5e0!3m2!1str!2str!4v1700000000000',
        help_text=_('Google Maps iframe src adresini buraya yapıştırın.'),
    )

    instagram = models.URLField(_('Instagram'), blank=True,
                                default='https://instagram.com/onmeryemek')
    facebook = models.URLField(_('Facebook'), blank=True,
                               default='https://facebook.com/onmeryemek')
    twitter = models.URLField(_('Twitter / X'), blank=True,
                              default='https://twitter.com/onmeryemek')
    youtube = models.URLField(_('YouTube'), blank=True,
                              default='https://youtube.com/@onmeryemek')

    about_short = models.TextField(
        _('Kısa Hakkımızda'),
        default='Onmer Yemek Organizasyon, lezzeti sanatla buluşturan '
                'premium bir catering markasıdır.',
    )
    about_long = models.TextField(
        _('Detaylı Hakkımızda'),
        default='20 yılı aşkın tecrübemizle düğünlerden kurumsal '
                'organizasyonlara, toplu yemek servislerinden özel davetlere '
                'kadar her boyuttaki etkinlik için kusursuz lezzetler '
                'hazırlıyoruz. Mutfağımızda yalnızca taze ve kaliteli '
                'malzemeler kullanırız.',
    )
    mission = models.TextField(
        _('Misyonumuz'),
        default='Misafirlerimize yalnızca yemek değil, unutulmaz bir deneyim '
                'sunmak; hijyen, lezzet ve sunum standartlarımızı her '
                'organizasyonda en üst seviyede tutmaktır.',
    )
    vision = models.TextField(
        _('Vizyonumuz'),
        default='Türkiye’nin en güvenilir premium catering markası olmak ve '
                'sektöre kalite çıtasını yükselten bir referans kazandırmak.',
    )

    class Meta:
        verbose_name = _('Site Ayarı')
        verbose_name_plural = _('Site Ayarları')

    def __str__(self) -> str:
        return self.company_name

    @classmethod
    def load(cls) -> 'SiteSetting':
        """Return the singleton row, creating it on first access."""
        instance, _created = cls.objects.get_or_create(pk=1)
        return instance

    def save(self, *args, **kwargs):
        # Force singleton behavior: there is only ever one site settings row.
        self.pk = 1
        super().save(*args, **kwargs)


class Statistic(models.Model):
    """Numeric counters displayed in the about / hero section."""

    label = models.CharField(_('Etiket'), max_length=80)
    value = models.PositiveIntegerField(_('Değer'))
    suffix = models.CharField(_('Sonek'), max_length=8, blank=True,
                              help_text=_('Örn: +, %, K'))
    icon = models.CharField(_('Bootstrap Icon Sınıfı'), max_length=80,
                            default='bi-award',
                            help_text=_('https://icons.getbootstrap.com adresinden seçin.'))
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)

    class Meta:
        verbose_name = _('İstatistik')
        verbose_name_plural = _('İstatistikler')
        ordering = ['order']

    def __str__(self) -> str:
        return f'{self.label}: {self.value}{self.suffix}'


class Service(models.Model):
    """Hero-level service tile shown on the home page."""

    title = models.CharField(_('Başlık'), max_length=120)
    short_description = models.CharField(_('Kısa Açıklama'), max_length=200)
    icon = models.CharField(_('Bootstrap Icon Sınıfı'), max_length=80,
                            default='bi-cup-hot',
                            help_text=_('https://icons.getbootstrap.com'))
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)
    is_active = models.BooleanField(_('Aktif'), default=True)

    class Meta:
        verbose_name = _('Hizmet')
        verbose_name_plural = _('Hizmetler')
        ordering = ['order']

    def __str__(self) -> str:
        return self.title


class ContactMessage(models.Model):
    """Inbound contact form submission."""

    full_name = models.CharField(_('Ad Soyad'), max_length=120)
    email = models.EmailField(_('E-posta'))
    phone = models.CharField(_('Telefon'), max_length=30, blank=True)
    subject = models.CharField(_('Konu'), max_length=200)
    message = models.TextField(_('Mesaj'))
    is_read = models.BooleanField(_('Okundu'), default=False)
    reply_text = models.TextField(_('Yanıt metni'), blank=True)
    replied_at = models.DateTimeField(_('Yanıt tarihi'), null=True, blank=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_replies',
        verbose_name=_('Yanıtlayan'),
    )
    created_at = models.DateTimeField(_('Gönderim Tarihi'), auto_now_add=True)

    class Meta:
        verbose_name = _('İletişim Mesajı')
        verbose_name_plural = _('İletişim Mesajları')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.full_name} – {self.subject}'

    @property
    def is_replied(self) -> bool:
        return bool(self.reply_text.strip())


class FleetVehicle(models.Model):
    """Vehicle in the delivery fleet shown on the logistics section."""

    name = models.CharField(_('Araç Adı / Modeli'), max_length=120)
    capacity = models.CharField(_('Kapasite'), max_length=120,
                                help_text=_('Örn: 500 kişilik servis'))
    icon = models.CharField(_('Bootstrap Icon Sınıfı'), max_length=80,
                            default='bi-truck')
    description = models.CharField(_('Açıklama'), max_length=255, blank=True)
    is_active = models.BooleanField(_('Aktif'), default=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)

    class Meta:
        verbose_name = _('Araç')
        verbose_name_plural = _('Araç Filosu')
        ordering = ['order']

    def __str__(self) -> str:
        return self.name


class ServiceArea(models.Model):
    """Geographical region the company serves."""

    name = models.CharField(_('Bölge / Şehir'), max_length=120)
    note = models.CharField(_('Not'), max_length=200, blank=True)
    is_active = models.BooleanField(_('Aktif'), default=True)
    order = models.PositiveSmallIntegerField(_('Sıra'), default=0)

    class Meta:
        verbose_name = _('Hizmet Bölgesi')
        verbose_name_plural = _('Hizmet Bölgeleri')
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return self.name
