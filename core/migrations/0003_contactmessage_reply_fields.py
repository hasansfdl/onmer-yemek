# Generated manually for ContactMessage reply fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0002_alter_sitesetting_google_maps_embed'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactmessage',
            name='reply_text',
            field=models.TextField(blank=True, verbose_name='Yanıt metni'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='replied_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Yanıt tarihi'),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='replied_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contact_replies',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Yanıtlayan',
            ),
        ),
    ]
