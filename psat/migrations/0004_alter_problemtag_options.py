# Generated by Django 4.2.4 on 2023-09-05 06:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('psat', '0003_auto_20230809_1343'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problemtag',
            options={'verbose_name': 'Tagged problem', 'verbose_name_plural': 'Tagged problems'},
        ),
    ]