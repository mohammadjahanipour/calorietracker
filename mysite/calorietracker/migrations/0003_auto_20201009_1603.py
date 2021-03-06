# Generated by Django 3.1.2 on 2020-10-09 16:03

import datetime
from django.db import migrations, models
import django_measurement.models
import measurement.measures.distance
import measurement.measures.mass


class Migration(migrations.Migration):

    dependencies = [
        ('calorietracker', '0002_auto_20201009_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='setting',
            name='activity',
            field=models.CharField(blank=True, choices=[('1', 'Sedentary (little or no exercise)'), ('2', 'Lightly active (light exercise/sports 1-3 days/week)'), ('3', 'Moderatetely active (moderate exercise/sports 3-5 days/week)'), ('4', 'Very active (hard exercise/sports 6-7 days a week)'), ('5', 'Extra active (very hard exercise/sports & physical job or 2x training)')], default='3', help_text='Used to estimate your total daily energy expenditure until we have enough data to calculate it', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='age',
            field=models.IntegerField(blank=True, default=30, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='goal',
            field=models.CharField(blank=True, choices=[('L', 'Lose'), ('M', 'Maintain'), ('G', 'Gain')], default='M', help_text='Do you want to lose, maintain, or gain weight?', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='goal_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='goal_weight',
            field=django_measurement.models.MeasurementField(blank=True, default=80, measurement=measurement.measures.mass.Mass, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='height',
            field=django_measurement.models.MeasurementField(blank=True, default=1.75, measurement=measurement.measures.distance.Distance, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='sex',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female')], default='M', max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='setting',
            name='unit_preference',
            field=models.CharField(blank=True, choices=[('I', 'Imperial'), ('M', 'Metric')], default='M', help_text='Display metric or imperial units on analytics page', max_length=1, null=True),
        ),
    ]
