# Generated by Django 5.0.1 on 2024-01-15 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('score', '0008_predictanswercount_rate_1_predictanswercount_rate_2_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predictanswercount',
            name='count_total',
            field=models.IntegerField(default=1),
        ),
    ]
