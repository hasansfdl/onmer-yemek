"""Kalp ikonlarını veritabanından kaldır."""

from django.db import migrations

ICON_REPLACEMENTS = {
    'bi-heart-fill': 'bi-calendar-event',
    'bi-suit-heart': 'bi-gem',
}


def replace_heart_icons(apps, schema_editor):
    Statistic = apps.get_model('core', 'Statistic')
    Service = apps.get_model('core', 'Service')
    MenuCategory = apps.get_model('menu', 'MenuCategory')

    for model in (Statistic, Service, MenuCategory):
        for old_icon, new_icon in ICON_REPLACEMENTS.items():
            model.objects.filter(icon=old_icon).update(icon=new_icon)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_contactmessage_reply_fields'),
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(replace_heart_icons, migrations.RunPython.noop),
    ]
