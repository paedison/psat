# Generated by Django 5.0.3 on 2024-07-19 11:56

import a_predict.models.base_settings
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_predict', '0003_psatexam_is_active'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PoliceAnswerCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('number', models.IntegerField(choices=a_predict.models.base_settings.ChoiceMethod.number_choices, default=1, verbose_name='번호')),
                ('answer', models.IntegerField(default=0, verbose_name='공식정답')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복표기')),
                ('count_total', models.IntegerField(default=0, verbose_name='총계')),
                ('all', models.JSONField(default=dict, verbose_name='전체')),
                ('filtered', models.JSONField(default=dict, verbose_name='필터링')),
                ('year', models.IntegerField(choices=a_predict.models.base_settings.ChoiceMethod.year_choices, default=2025, verbose_name='연도')),
                ('exam', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_exam_choices, default='경위', max_length=2, verbose_name='시험')),
                ('subject', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_subject_choices, default='hyeongsa', max_length=20, verbose_name='과목')),
            ],
            options={
                'verbose_name': '경위공채 성적예측 [5] 답안개수',
                'verbose_name_plural': '경위공채 성적예측 [5] 답안개수',
                'db_table': 'a_predict_police_answer_count',
            },
            bases=(models.Model, a_predict.models.base_settings.ChoiceMethod),
        ),
        migrations.CreateModel(
            name='PoliceDepartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('remarks', models.TextField(blank=True, null=True, verbose_name='주석')),
                ('order', models.IntegerField()),
                ('exam', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_exam_choices, default='경위', max_length=2, verbose_name='시험')),
                ('unit', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_unit_choices, default='경위', max_length=20, verbose_name='모집단위')),
                ('name', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_department_choices, default='일반', max_length=40, verbose_name='직렬')),
            ],
            options={
                'verbose_name': '경위공채 성적예측 [3] 직렬',
                'verbose_name_plural': '경위공채 성적예측 [3] 직렬',
                'db_table': 'a_predict_police_department',
            },
        ),
        migrations.CreateModel(
            name='PoliceExam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('answer_official', models.JSONField(default=dict)),
                ('page_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam_started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam_finished_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer_predict_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer_official_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('participants', models.JSONField(default=dict, verbose_name='전체 참여자수')),
                ('statistics', models.JSONField(default=dict, verbose_name='성적 통계')),
                ('is_active', models.BooleanField(default=True)),
                ('year', models.IntegerField(choices=a_predict.models.base_settings.ChoiceMethod.year_choices, default=2025, verbose_name='연도')),
                ('exam', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_exam_choices, default='경위', max_length=2, verbose_name='시험')),
            ],
            options={
                'verbose_name': '경위공채 성적예측 [1] 시험',
                'verbose_name_plural': '경위공채 성적예측 [1] 시험',
                'db_table': 'a_predict_police_exam',
            },
        ),
        migrations.CreateModel(
            name='PoliceUnit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('remarks', models.TextField(blank=True, null=True, verbose_name='주석')),
                ('order', models.IntegerField()),
                ('exam', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_exam_choices, default='경위', max_length=2, verbose_name='시험')),
                ('name', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_unit_choices, default='경위', max_length=20, verbose_name='모집단위')),
            ],
            options={
                'verbose_name': '경위공채 성적예측 [2] 모집단위',
                'verbose_name_plural': '경위공채 성적예측 [2] 모집단위',
                'db_table': 'a_predict_police_unit',
            },
        ),
        migrations.AlterField(
            model_name='psatunit',
            name='name',
            field=models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.psat_unit_choices, default='5급 행정(전국)', max_length=20, verbose_name='모집단위'),
        ),
        migrations.CreateModel(
            name='PoliceStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('remarks', models.TextField(blank=True, null=True, verbose_name='주석')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('name', models.CharField(max_length=20, verbose_name='이름')),
                ('serial', models.CharField(max_length=10, verbose_name='수험번호')),
                ('password', models.CharField(blank=True, max_length=10, null=True, verbose_name='비밀번호')),
                ('prime_id', models.CharField(blank=True, max_length=15, null=True, verbose_name='프라임 ID')),
                ('answer', models.JSONField(default=dict, verbose_name='답안')),
                ('answer_count', models.JSONField(default=dict, verbose_name='답안 개수')),
                ('answer_confirmed', models.JSONField(default=dict, verbose_name='답안 확정')),
                ('answer_all_confirmed_at', models.DateTimeField(blank=True, null=True, verbose_name='답안 전체 확정 일시')),
                ('score', models.JSONField(default=dict, verbose_name='점수')),
                ('rank', models.JSONField(default=dict, verbose_name='등수')),
                ('year', models.IntegerField(choices=a_predict.models.base_settings.ChoiceMethod.year_choices, default=2025, verbose_name='연도')),
                ('exam', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_exam_choices, default='경위', max_length=2, verbose_name='시험')),
                ('unit', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_unit_choices, default='경위', max_length=20, verbose_name='모집단위')),
                ('department', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_department_choices, default='일반', max_length=40, verbose_name='직렬')),
                ('selection', models.CharField(choices=a_predict.models.base_settings.ChoiceMethod.police_subject_choices, default='minbeob', max_length=20, verbose_name='선택과목')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '경위공채 성적예측 [4] 수험정보',
                'verbose_name_plural': '경위공채 성적예측 [4] 수험정보',
                'db_table': 'a_predict_police_student',
            },
            bases=(models.Model, a_predict.models.base_settings.ChoiceMethod),
        ),
    ]