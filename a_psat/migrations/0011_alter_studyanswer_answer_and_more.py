# Generated by Django 5.1 on 2025-02-13 02:38

import a_psat.models.choices
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_psat', '0010_studyorganization_studyanswercount_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studyanswer',
            name='answer',
            field=models.IntegerField(choices=a_psat.models.choices.answer_choice, default=0, verbose_name='답안'),
        ),
        migrations.AlterField(
            model_name='studystudent',
            name='curriculum',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='a_psat.studycurriculum'),
        ),
    ]
