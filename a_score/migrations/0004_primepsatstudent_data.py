# Generated by Django 5.0.3 on 2024-07-24 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_score', '0003_primepoliceanswercount_all_primepoliceexam_is_active_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='primepsatstudent',
            name='data',
            field=models.JSONField(default=list, verbose_name='답안 자료'),
        ),
    ]