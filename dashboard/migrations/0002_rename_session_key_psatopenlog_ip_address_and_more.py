# Generated by Django 4.2.5 on 2023-10-31 10:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='psatopenlog',
            old_name='session_key',
            new_name='ip_address',
        ),
        migrations.RemoveField(
            model_name='psatlikelog',
            name='session_key',
        ),
        migrations.RemoveField(
            model_name='psatratelog',
            name='session_key',
        ),
        migrations.RemoveField(
            model_name='psatsolvelog',
            name='session_key',
        ),
    ]
