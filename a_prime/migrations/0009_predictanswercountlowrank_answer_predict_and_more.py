# Generated by Django 5.1 on 2024-12-27 03:38

import django.db.models.functions.comparison
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_prime', '0008_alter_resultstatistics_average_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='predictanswercountlowrank',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
        migrations.AddField(
            model_name='predictanswercountmidrank',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
        migrations.AddField(
            model_name='predictanswercounttoprank',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
        migrations.AddField(
            model_name='resultanswercount',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
        migrations.AddField(
            model_name='resultanswercountlowrank',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
        migrations.AddField(
            model_name='resultanswercountmidrank',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
        migrations.AddField(
            model_name='resultanswercounttoprank',
            name='answer_predict',
            field=models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField()),
        ),
    ]
