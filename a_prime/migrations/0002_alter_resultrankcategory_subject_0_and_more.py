# Generated by Django 5.1 on 2024-12-07 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_prime', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resultrankcategory',
            name='subject_0',
            field=models.IntegerField(blank=True, null=True, verbose_name='헌법'),
        ),
        migrations.AlterField(
            model_name='resultrankcategory',
            name='subject_1',
            field=models.IntegerField(blank=True, null=True, verbose_name='언어논리'),
        ),
        migrations.AlterField(
            model_name='resultrankcategory',
            name='subject_2',
            field=models.IntegerField(blank=True, null=True, verbose_name='자료해석'),
        ),
        migrations.AlterField(
            model_name='resultrankcategory',
            name='subject_3',
            field=models.IntegerField(blank=True, null=True, verbose_name='상황판단'),
        ),
        migrations.AlterField(
            model_name='resultrankcategory',
            name='total',
            field=models.IntegerField(blank=True, null=True, verbose_name='PSAT'),
        ),
        migrations.AlterField(
            model_name='resultranktotal',
            name='subject_0',
            field=models.IntegerField(blank=True, null=True, verbose_name='헌법'),
        ),
        migrations.AlterField(
            model_name='resultranktotal',
            name='subject_1',
            field=models.IntegerField(blank=True, null=True, verbose_name='언어논리'),
        ),
        migrations.AlterField(
            model_name='resultranktotal',
            name='subject_2',
            field=models.IntegerField(blank=True, null=True, verbose_name='자료해석'),
        ),
        migrations.AlterField(
            model_name='resultranktotal',
            name='subject_3',
            field=models.IntegerField(blank=True, null=True, verbose_name='상황판단'),
        ),
        migrations.AlterField(
            model_name='resultranktotal',
            name='total',
            field=models.IntegerField(blank=True, null=True, verbose_name='PSAT'),
        ),
    ]
