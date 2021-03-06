# Generated by Django 3.1.2 on 2020-10-17 16:19

from django.db import migrations

# from django.conf import settings

# important sets the site domain and name


def set_site_name(apps, schema_editor):
    SiteModel = apps.get_model('sites', 'Site')

    # Production
    domain = 'Calorietracker.io'
    name = "Calorietracker"

    # Development
    dev_domain = "127.0.0.1:8000"
    dev_name = "DEVCalorietracker"

    SiteModel.objects.update_or_create(
        pk=1,
        defaults={'domain': dev_domain,
                  'name': dev_name}
    )

    SiteModel.objects.update_or_create(
        pk=2,
        defaults={'domain': domain,
                  'name': name}
    )


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),  # Required to reference `sites` in `apps.get_model()`
        ('calorietracker', '0006_auto_20201014_0650'),
    ]

    operations = [
        migrations.RunPython(set_site_name),
    ]
