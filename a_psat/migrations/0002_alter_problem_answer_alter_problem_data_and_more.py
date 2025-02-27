# Generated by Django 5.1 on 2024-10-23 12:35

import a_psat.models.choices
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_psat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='answer',
            field=models.IntegerField(choices=a_psat.models.choices.answer_choice, default=1, verbose_name='정답'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='data',
            field=models.TextField(verbose_name='자료'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='exam',
            field=models.CharField(choices=[('행시', '5급공채/행정고시'), ('입시', '입법고시'), ('칠급', '7급공채'), ('칠예', '7급공채 예시'), ('민경', '민간경력'), ('외시', '외교원/외무고시'), ('견습', '견습')], default='행시', max_length=2, verbose_name='시험'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='number',
            field=models.IntegerField(choices=a_psat.models.choices.number_choice, default=1, verbose_name='번호'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='paper_type',
            field=models.CharField(default='', max_length=2, verbose_name='책형'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='question',
            field=models.TextField(verbose_name='발문'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='subject',
            field=models.CharField(choices=[('헌법', '헌법'), ('언어', '언어논리'), ('자료', '자료해석'), ('상황', '상황판단')], default='언어', max_length=2, verbose_name='과목'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='year',
            field=models.IntegerField(choices=a_psat.models.choices.year_choice, default=2024, verbose_name='연도'),
        ),
        migrations.CreateModel(
            name='Psat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(choices=a_psat.models.choices.year_choice, default=2024, verbose_name='연도')),
                ('exam', models.CharField(choices=a_psat.models.choices.exam_choice, default='행시', max_length=2, verbose_name='시험')),
                ('order', models.IntegerField(verbose_name='순서')),
                ('is_active', models.BooleanField(default=False, verbose_name='활성')),
            ],
            options={
                'verbose_name': '00_PSAT',
                'verbose_name_plural': '00_PSAT',
                'ordering': ['-year', 'order'],
                'constraints': [models.UniqueConstraint(fields=('year', 'exam'), name='unique_psat')],
            },
        ),
    ]
