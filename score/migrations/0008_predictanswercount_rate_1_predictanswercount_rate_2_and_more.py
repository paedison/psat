# Generated by Django 5.0.1 on 2024-01-15 03:55

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('score', '0007_predictanswercount_predictstudent_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictanswercount',
            name='rate_1',
            field=models.GeneratedField(db_persist=False, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('count_1'), '*', models.Value(100)), '/', models.F('count_total')), output_field=models.FloatField()),
        ),
        migrations.AddField(
            model_name='predictanswercount',
            name='rate_2',
            field=models.GeneratedField(db_persist=False, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('count_2'), '*', models.Value(100)), '/', models.F('count_total')), output_field=models.FloatField()),
        ),
        migrations.AddField(
            model_name='predictanswercount',
            name='rate_3',
            field=models.GeneratedField(db_persist=False, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('count_3'), '*', models.Value(100)), '/', models.F('count_total')), output_field=models.FloatField()),
        ),
        migrations.AddField(
            model_name='predictanswercount',
            name='rate_4',
            field=models.GeneratedField(db_persist=False, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('count_4'), '*', models.Value(100)), '/', models.F('count_total')), output_field=models.FloatField()),
        ),
        migrations.AddField(
            model_name='predictanswercount',
            name='rate_5',
            field=models.GeneratedField(db_persist=False, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('count_5'), '*', models.Value(100)), '/', models.F('count_total')), output_field=models.FloatField()),
        ),
    ]