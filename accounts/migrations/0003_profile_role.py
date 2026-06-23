"""Profil yetki alanı ve mevcut kullanıcılar için başlangıç değerleri."""

from django.db import migrations, models


def sync_roles_from_users(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    for profile in Profile.objects.select_related('user').iterator():
        user = profile.user
        if user.is_superuser:
            role = 'admin'
        elif user.is_staff:
            role = 'staff'
        else:
            role = 'member'
        if profile.role != role:
            Profile.objects.filter(pk=profile.pk).update(role=role)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_backfill_profiles'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[
                    ('member', 'Üye'),
                    ('staff', 'Yönetim Paneli'),
                    ('admin', 'Tam Yetki'),
                ],
                default='member',
                help_text='Yönetim paneli ve tam yetki yalnızca güvenilir hesaplara verilmelidir.',
                max_length=20,
                verbose_name='Yetki',
            ),
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={
                'verbose_name': 'Kullanıcı',
                'verbose_name_plural': 'Kullanıcılar',
            },
        ),
        migrations.RunPython(sync_roles_from_users, migrations.RunPython.noop),
    ]
