# Generated by Django 5.0.1 on 2024-01-23 11:43

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('score', '0011_alter_predictanswercount_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='primeanswercount',
            name='rate_0',
            field=models.GeneratedField(db_persist=False, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('count_0'), '*', models.Value(100)), '/', models.F('count_total')), output_field=models.FloatField()),
        ),
    ]
