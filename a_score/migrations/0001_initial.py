# Generated by Django 5.0.3 on 2024-07-04 08:17

import a_score.models.base_settings
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PrimePoliceAnswerCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('number', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.number_choices, default=1, verbose_name='문제 번호')),
                ('answer', models.IntegerField(blank=True, null=True, verbose_name='정답')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복 표기')),
                ('count_total', models.IntegerField(default=0, verbose_name='전체')),
                ('year', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.year_choices, default=2025, verbose_name='연도')),
                ('exam', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_police_exam_choices, default='프모', max_length=2, verbose_name='시험')),
                ('subject', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_police_subject_choices, default='형사', max_length=10, verbose_name='과목')),
            ],
            options={
                'verbose_name': '프라임 경위공채 모의고사 답안 개수',
                'verbose_name_plural': '프라임 경위공채 모의고사 답안 개수',
                'db_table': 'a_score_prime_police_answer_count',
            },
            bases=(models.Model, a_score.models.base_settings.ChoiceMethod),
        ),
        migrations.CreateModel(
            name='PrimePoliceExam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('answer_official', models.JSONField(default=dict)),
                ('page_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam_started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam_finished_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer_predict_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer_official_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('year', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.year_choices, default=2025, verbose_name='연도')),
                ('exam', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_police_exam_choices, default='프모', max_length=2, verbose_name='시험')),
            ],
            options={
                'verbose_name': '프라임 경위공채 모의고사',
                'verbose_name_plural': '프라임 경위공채 모의고사',
                'db_table': 'a_score_prime_police_exam',
            },
        ),
        migrations.CreateModel(
            name='PrimePoliceStudent',
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
                ('rank_total', models.JSONField(default=dict, verbose_name='전체 등수')),
                ('rank_department', models.JSONField(default=dict, verbose_name='직렬 등수')),
                ('participants_total', models.JSONField(default=dict, verbose_name='전체 참여자수')),
                ('participants_department', models.JSONField(default=dict, verbose_name='직렬 참여자수')),
                ('year', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.year_choices, default=2025, verbose_name='연도')),
                ('exam', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_police_exam_choices, default='프모', max_length=2, verbose_name='시험')),
                ('unit', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.police_unit_choices, default='경위', max_length=10, verbose_name='모집단위')),
                ('department', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_police_department_choices, default='일반', max_length=20, verbose_name='직렬')),
            ],
            options={
                'verbose_name': '프라임 경위공채 모의고사 수험정보',
                'verbose_name_plural': '프라임 경위공채 모의고사 수험정보',
                'db_table': 'a_score_prime_police_student',
            },
            bases=(models.Model, a_score.models.base_settings.ChoiceMethod),
        ),
        migrations.CreateModel(
            name='PrimePsatAnswerCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('number', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.number_choices, default=1, verbose_name='문제 번호')),
                ('answer', models.IntegerField(blank=True, null=True, verbose_name='정답')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_5', models.IntegerField(default=0, verbose_name='⑤')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복 표기')),
                ('count_total', models.IntegerField(default=0, verbose_name='전체')),
                ('year', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.year_choices, default=2024, verbose_name='연도')),
                ('exam', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_psat_exam_choices, default='프모', max_length=2, verbose_name='시험')),
                ('subject', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.psat_subject_choices, default='heonbeob', max_length=20, verbose_name='과목')),
            ],
            options={
                'verbose_name': '프라임 PSAT 모의고사 답안 개수',
                'verbose_name_plural': '프라임 PSAT 모의고사 답안 개수',
                'db_table': 'a_score_prime_psat_answer_count',
            },
            bases=(models.Model, a_score.models.base_settings.ChoiceMethod),
        ),
        migrations.CreateModel(
            name='PrimePsatExam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round', models.IntegerField(default=0, verbose_name='회차')),
                ('answer_official', models.JSONField(default=dict)),
                ('page_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam_started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('exam_finished_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer_predict_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer_official_opened_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('year', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.year_choices, default=2024, verbose_name='연도')),
                ('exam', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_psat_exam_choices, default='프모', max_length=2, verbose_name='시험')),
            ],
            options={
                'verbose_name': '프라임 PSAT 모의고사',
                'verbose_name_plural': '프라임 PSAT 모의고사',
                'db_table': 'a_score_prime_psat_exam',
            },
        ),
        migrations.CreateModel(
            name='PrimePsatStudent',
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
                ('rank_total', models.JSONField(default=dict, verbose_name='전체 등수')),
                ('rank_department', models.JSONField(default=dict, verbose_name='직렬 등수')),
                ('participants_total', models.JSONField(default=dict, verbose_name='전체 참여자수')),
                ('participants_department', models.JSONField(default=dict, verbose_name='직렬 참여자수')),
                ('year', models.IntegerField(choices=a_score.models.base_settings.ChoiceMethod.year_choices, default=2024, verbose_name='연도')),
                ('exam', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_psat_exam_choices, default='프모', max_length=2, verbose_name='시험')),
                ('unit', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_psat_unit_choices, default='5급공채', max_length=10, verbose_name='모집단위')),
                ('department', models.CharField(choices=a_score.models.base_settings.ChoiceMethod.prime_psat_department_choices, default='일반행정', max_length=20, verbose_name='직렬')),
            ],
            options={
                'verbose_name': '프라임 PSAT 모의고사 수험정보',
                'verbose_name_plural': '프라임 PSAT 모의고사 수험정보',
                'db_table': 'a_score_prime_psat_student',
            },
            bases=(models.Model, a_score.models.base_settings.ChoiceMethod),
        ),
        migrations.CreateModel(
            name='PrimePoliceRegisteredStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prime_police_registered_students', to=settings.AUTH_USER_MODEL, verbose_name='회원정보')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registered_students', to='a_score.primepolicestudent', verbose_name='수험정보')),
            ],
            options={
                'verbose_name': '프라임 경위공채 모의고사 수험정보 연결',
                'verbose_name_plural': '프라임 경위공채 모의고사 수험정보 연결',
                'db_table': 'a_score_prime_police_registered_student',
                'unique_together': {('user', 'student')},
            },
        ),
        migrations.CreateModel(
            name='PrimePsatRegisteredStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prime_psat_registered_students', to=settings.AUTH_USER_MODEL, verbose_name='회원정보')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registered_students', to='a_score.primepsatstudent', verbose_name='수험정보')),
            ],
            options={
                'verbose_name': '프라임 PSAT 모의고사 수험정보 연결',
                'verbose_name_plural': '프라임 PSAT 모의고사 수험정보 연결',
                'db_table': 'a_score_prime_psat_registered_student',
                'unique_together': {('user', 'student')},
            },
        ),
    ]
