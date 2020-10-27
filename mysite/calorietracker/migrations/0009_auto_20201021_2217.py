# Generated by Django 3.1.2 on 2020-10-21 22:17

import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calorietracker', '0008_wallet'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted', models.DateTimeField(editable=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('Image', cloudinary.models.CloudinaryField(max_length=255, verbose_name='image')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='log',
            name='log_progress_pic',
            field=cloudinary.models.CloudinaryField(max_length=255, null=True, verbose_name='image'),
        ),
    ]