"""Populate the project with realistic demo content for the showcase site.

Usage:
    python manage.py seed_demo
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Service,
    SiteSetting,
    Statistic,
)
from menu.models import Dish, MenuCategory


class Command(BaseCommand):
    help = 'Seed demo content for the Onmer catering website.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('==> Onmer demo verisi yukleniyor...'))

        # ----- Site setting (singleton) -----
        SiteSetting.load()

        # ----- Statistics -----
        stats = [
            ('Tamamlanan Organizasyon', 1250, '+', 'bi-trophy', 1),
            ('Mutlu Müşteri', 9800, '+', 'bi-emoji-smile', 2),
            ('Yıllık Tecrübe', 20, '+', 'bi-award', 3),
            ('Şef & Personel', 65, '+', 'bi-people', 4),
        ]
        Statistic.objects.all().delete()
        for label, value, suffix, icon, order in stats:
            Statistic.objects.create(
                label=label, value=value, suffix=suffix, icon=icon, order=order,
            )

        # ----- Services -----
        services = [
            ('Düğün Organizasyonları', 'Hayalinizdeki düğün için özenle hazırlanmış zarif menüler ve kusursuz sunum.', 'bi-heart-fill'),
            ('Nişan & Söz Yemeği', 'Aileler için sade, lezzet dolu ve şık nişan menüleri.', 'bi-suit-heart'),
            ('Kurumsal Catering', 'Açılış kokteylleri, iş yemekleri ve özel kurumsal davetler.', 'bi-building-fill'),
            ('Toplu Yemek Servisi', 'Fabrika, ofis ve okullar için hijyenik, lezzetli toplu yemek.', 'bi-people-fill'),
            ('Catering Hizmeti', 'Etkinliğinize özel mobil mutfak ve catering ekibi.', 'bi-truck'),
            ('Özel Davet & Parti', 'Özel günleriniz için butik menüler ve sunum.', 'bi-stars'),
        ]
        Service.objects.all().delete()
        for i, (title, desc, icon) in enumerate(services):
            Service.objects.create(title=title, short_description=desc,
                                   icon=icon, order=i, is_active=True)

        # ----- Categories -----
        category_specs = [
            ('Düğün', 'wedding', 'bi-heart-fill', 1),
            ('Nişan', 'engagement', 'bi-suit-heart', 2),
            ('Şirket Organizasyonu', 'corporate', 'bi-building', 3),
            ('Toplu Yemek', 'bulk', 'bi-people-fill', 4),
            ('Catering', 'catering', 'bi-truck', 5),
        ]
        cats = {}
        for name, kind, icon, order in category_specs:
            cat, _ = MenuCategory.objects.update_or_create(
                kind=kind,
                defaults={'name': name, 'icon': icon, 'order': order,
                          'is_active': True},
            )
            cats[kind] = cat

        # ----- Dishes -----
        dishes = [
            ('Tandır Kuzu', 'wedding',
             'Saatlerce ağır ateşte pişen geleneksel tandır kuzu. '
             'Pirinç pilavı ve közlenmiş sebzelerle servis edilir.',
             'kuzu eti, pirinç, soğan, baharat',
             720, '300 gr / kişi', True),
            ('İçli Köfte', 'engagement',
             'El emeği ince bulgur kabuk içinde özel ceviz ve baharatlı iç harç.',
             'bulgur, kıyma, ceviz, baharat',
             420, '2 adet / kişi', True),
            ('Sea Bass Carpaccio', 'corporate',
             'İnce dilimlenmiş taze levrek, limon, sızma zeytinyağı ve dereotu ile.',
             'levrek, limon, zeytinyağı, dereotu',
             280, '120 gr / kişi', True),
            ('Mantı – Kayseri Usulü', 'bulk',
             'Geleneksel el açması mantı, sarımsaklı yoğurt ve tereyağlı sos.',
             'un, kıyma, yoğurt, tereyağ',
             550, '200 gr / kişi', False),
            ('Şef Antipasti Tabağı', 'corporate',
             'Mevsim sebzeleri, peynirler, jambon ve özel ev usulü reçellerle.',
             'sebze, peynir, jambon, reçel',
             320, 'Tabak', False),
            ('Künefe', 'wedding',
             'Hatay\'dan getirtilen kadayıf, taze tuzsuz peynir ve antep fıstığı.',
             'kadayıf, peynir, şerbet, antep fıstığı',
             390, '1 adet / kişi', True),
        ]
        # Reset previously seeded dishes only.
        Dish.objects.filter(name__in=[d[0] for d in dishes]).delete()
        sample_imgs = [
            'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1565958011703-44f9829ba187?auto=format&fit=crop&w=800&q=80',
        ]
        for i, (name, cat_key, desc, ing, kcal, serve, featured) in enumerate(dishes):
            Dish.objects.create(
                category=cats.get(cat_key),
                name=name,
                description=desc,
                ingredients=ing,
                calories=kcal,
                serving_size=serve,
                is_featured=featured,
                is_active=True,
                order=i,
            )
        self.stdout.write(self.style.SUCCESS(
            'NOT: Yemek görselleri admin panelinden yüklenebilir. '
            f'Demo için referans görseller: {", ".join(sample_imgs[:2])}'
        ))

        self.stdout.write(self.style.SUCCESS(
            'OK: Demo verisi basariyla yuklendi. Admin panelinden gorseller ekleyebilirsiniz.'
        ))
