# Generated by Django 5.0.3 on 2024-08-11 07:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('a_psat', '0003_alter_problemtaggeditem_content_object_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problemcollection',
            options={'ordering': ['user', 'order']},
        ),
    ]