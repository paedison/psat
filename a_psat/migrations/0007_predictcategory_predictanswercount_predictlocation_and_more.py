# Generated by Django 5.1 on 2024-11-07 02:48

import a_psat.models.choices
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_psat', '0006_alter_lecture_options_alter_lecturelike_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PredictCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exam', models.CharField(choices=a_psat.models.choices.predict_exam_choice, default='행시', max_length=2, verbose_name='시험')),
                ('unit', models.CharField(choices=a_psat.models.choices.predict_unit_choice, default='5급 행정', max_length=20, verbose_name='모집단위')),
                ('department', models.CharField(default='일반행정', max_length=40, verbose_name='직렬')),
                ('order', models.SmallIntegerField(default=1, verbose_name='순서')),
            ],
            options={
                'verbose_name': '[합격예측] 01_모집단위 및 직렬',
                'verbose_name_plural': '[합격예측] 01_모집단위 및 직렬',
                'db_table': 'a_psat_predict_category',
            },
        ),
        migrations.CreateModel(
            name='PredictAnswerCount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_5', models.IntegerField(default=0, verbose_name='⑤')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복표기')),
                ('count_total', models.IntegerField(default=0, verbose_name='총계')),
                ('problem', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answer_counts', to='a_psat.problem')),
            ],
            options={
                'verbose_name': '[합격예측] 04_답안 개수',
                'verbose_name_plural': '[합격예측] 04_답안 개수',
                'db_table': 'a_psat_predict_answer_count',
            },
        ),
        migrations.CreateModel(
            name='PredictLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_start', models.IntegerField(verbose_name='시작 수험번호')),
                ('serial_end', models.IntegerField(verbose_name='마지막 수험번호')),
                ('region', models.CharField(max_length=10, verbose_name='지역')),
                ('school', models.CharField(max_length=30, verbose_name='학교명')),
                ('address', models.CharField(max_length=50, verbose_name='주소')),
                ('contact', models.CharField(blank=True, max_length=20, null=True, verbose_name='연락처')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='a_psat.predictcategory', verbose_name='모집단위·직렬')),
                ('psat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predict_locations', to='a_psat.psat')),
            ],
            options={
                'verbose_name': '[합격예측] 08_시험 장소',
                'verbose_name_plural': '[합격예측] 08_시험 장소',
                'db_table': 'a_psat_predict_location',
            },
        ),
        migrations.CreateModel(
            name='PredictPsat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_opened_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='페이지 오픈 일시')),
                ('exam_started_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='시험 시작 일시')),
                ('exam_finished_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='시험 종료 일시')),
                ('answer_predict_opened_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='예상 정답 공개 일시')),
                ('answer_official_opened_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='공식 정답 공개 일시')),
                ('psat', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='predict_psat', to='a_psat.psat')),
            ],
            options={
                'verbose_name': '[합격예측] 00_PSAT',
                'verbose_name_plural': '[합격예측] 00_PSAT',
                'db_table': 'a_psat_predict_psat',
            },
        ),
        migrations.CreateModel(
            name='PredictStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, verbose_name='이름')),
                ('serial', models.CharField(max_length=10, verbose_name='수험번호')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='a_psat.predictcategory')),
                ('psat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predict_students', to='a_psat.psat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='psat_predict_students', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '[합격예측] 02_수험정보',
                'verbose_name_plural': '[합격예측] 02_수험정보',
                'db_table': 'a_psat_predict_student',
            },
        ),
        migrations.CreateModel(
            name='PredictScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.FloatField(blank=True, null=True, verbose_name='헌법')),
                ('subject_1', models.FloatField(blank=True, null=True, verbose_name='언어논리')),
                ('subject_2', models.FloatField(blank=True, null=True, verbose_name='자료해석')),
                ('subject_3', models.FloatField(blank=True, null=True, verbose_name='상황판단')),
                ('total', models.FloatField(blank=True, null=True, verbose_name='PSAT 총점')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='score', to='a_psat.predictstudent')),
            ],
            options={
                'verbose_name': '[합격예측] 05_점수',
                'verbose_name_plural': '[합격예측] 05_점수',
                'db_table': 'a_psat_predict_score',
            },
        ),
        migrations.CreateModel(
            name='PredictRankTotal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.FloatField(blank=True, null=True, verbose_name='헌법')),
                ('subject_1', models.FloatField(blank=True, null=True, verbose_name='언어논리')),
                ('subject_2', models.FloatField(blank=True, null=True, verbose_name='자료해석')),
                ('subject_3', models.FloatField(blank=True, null=True, verbose_name='상황판단')),
                ('total', models.FloatField(blank=True, null=True, verbose_name='PSAT')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_totals', to='a_psat.predictstudent')),
            ],
            options={
                'verbose_name': '[합격예측] 06_전체 등수',
                'verbose_name_plural': '[합격예측] 06_전체 등수',
                'db_table': 'a_psat_predict_rank_total',
            },
        ),
        migrations.CreateModel(
            name='PredictRankCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.FloatField(blank=True, null=True, verbose_name='헌법')),
                ('subject_1', models.FloatField(blank=True, null=True, verbose_name='언어논리')),
                ('subject_2', models.FloatField(blank=True, null=True, verbose_name='자료해석')),
                ('subject_3', models.FloatField(blank=True, null=True, verbose_name='상황판단')),
                ('total', models.FloatField(blank=True, null=True, verbose_name='PSAT')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_categories', to='a_psat.predictstudent')),
            ],
            options={
                'verbose_name': '[합격예측] 07_직렬 등수',
                'verbose_name_plural': '[합격예측] 07_직렬 등수',
                'db_table': 'a_psat_predict_rank_category',
            },
        ),
        migrations.CreateModel(
            name='PredictAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.IntegerField(choices=a_psat.models.choices.answer_choice, default=1, verbose_name='답안')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answers', to='a_psat.problem')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='a_psat.predictstudent')),
            ],
            options={
                'verbose_name': '[합격예측] 03_답안',
                'verbose_name_plural': '[합격예측] 03_답안',
                'db_table': 'a_psat_predict_answer',
            },
        ),
    ]