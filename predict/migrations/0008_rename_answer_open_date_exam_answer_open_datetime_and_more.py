# Generated by Django 5.0.2 on 2024-02-29 01:39

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predict', '0007_student_prime_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exam',
            old_name='answer_open_date',
            new_name='answer_open_datetime',
        ),
        migrations.RenameField(
            model_name='exam',
            old_name='predict_open_date',
            new_name='predict_open_datetime',
        ),
        migrations.RenameField(
            model_name='exam',
            old_name='exam_date',
            new_name='start_datetime',
        ),
        migrations.AddField(
            model_name='exam',
            name='end_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]