# Generated by Django 5.0.3 on 2024-04-16 08:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('psat', '0015_comment_title'),
        ('reference', '0005_unit_unitdepartment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user_id', models.IntegerField()),
                ('title', models.CharField(max_length=20)),
                ('order', models.IntegerField()),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['user_id', 'order'],
                'unique_together': {('user_id', 'title')},
            },
        ),
        migrations.CreateModel(
            name='CollectionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.IntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('collection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collection_items', to='psat.collection')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collection_items', to='reference.psatproblem')),
            ],
            options={
                'ordering': ['collection__user_id', 'collection', 'order'],
            },
        ),
    ]
