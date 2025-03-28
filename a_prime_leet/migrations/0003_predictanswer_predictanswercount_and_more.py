# Generated by Django 5.1 on 2025-03-18 11:43

import a_prime_leet.models.abstract_models
import a_prime_leet.models.choices
import django.db.models.deletion
import django.db.models.functions.comparison
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('a_prime_leet', '0002_alter_leet_round_alter_leet_year'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PredictAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='작성 일시')),
                ('answer', models.IntegerField(choices=a_prime_leet.models.choices.answer_choice, default=1, verbose_name='답안')),
            ],
            options={
                'verbose_name': '[성적예측] 03_답안',
                'verbose_name_plural': '[성적예측] 03_답안',
                'db_table': 'a_prime_leet_predict_answer',
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
                ('count_sum', models.IntegerField(default=0, verbose_name='총계')),
                ('answer_predict', models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField())),
                ('filtered_count_1', models.IntegerField(default=0, verbose_name='[필터링]①')),
                ('filtered_count_2', models.IntegerField(default=0, verbose_name='[필터링]②')),
                ('filtered_count_3', models.IntegerField(default=0, verbose_name='[필터링]③')),
                ('filtered_count_4', models.IntegerField(default=0, verbose_name='[필터링]④')),
                ('filtered_count_5', models.IntegerField(default=0, verbose_name='[필터링]⑤')),
                ('filtered_count_0', models.IntegerField(default=0, verbose_name='[필터링]미표기')),
                ('filtered_count_multiple', models.IntegerField(default=0, verbose_name='[필터링]중복표기')),
                ('filtered_count_sum', models.IntegerField(default=0, verbose_name='[필터링]총계')),
            ],
            options={
                'verbose_name': '[성적예측] 04_답안 개수',
                'verbose_name_plural': '[성적예측] 04_답안 개수',
                'db_table': 'a_prime_leet_predict_answer_count',
            },
        ),
        migrations.CreateModel(
            name='PredictAnswerCountLowRank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_5', models.IntegerField(default=0, verbose_name='⑤')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복표기')),
                ('count_sum', models.IntegerField(default=0, verbose_name='총계')),
                ('answer_predict', models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField())),
                ('filtered_count_1', models.IntegerField(default=0, verbose_name='[필터링]①')),
                ('filtered_count_2', models.IntegerField(default=0, verbose_name='[필터링]②')),
                ('filtered_count_3', models.IntegerField(default=0, verbose_name='[필터링]③')),
                ('filtered_count_4', models.IntegerField(default=0, verbose_name='[필터링]④')),
                ('filtered_count_5', models.IntegerField(default=0, verbose_name='[필터링]⑤')),
                ('filtered_count_0', models.IntegerField(default=0, verbose_name='[필터링]미표기')),
                ('filtered_count_multiple', models.IntegerField(default=0, verbose_name='[필터링]중복표기')),
                ('filtered_count_sum', models.IntegerField(default=0, verbose_name='[필터링]총계')),
            ],
            options={
                'verbose_name': '[성적예측] 11_답안 개수(하위권)',
                'verbose_name_plural': '[성적예측] 11_답안 개수(하위권)',
                'db_table': 'a_prime_leet_predict_answer_count_low_rank',
            },
        ),
        migrations.CreateModel(
            name='PredictAnswerCountMidRank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_5', models.IntegerField(default=0, verbose_name='⑤')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복표기')),
                ('count_sum', models.IntegerField(default=0, verbose_name='총계')),
                ('answer_predict', models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField())),
                ('filtered_count_1', models.IntegerField(default=0, verbose_name='[필터링]①')),
                ('filtered_count_2', models.IntegerField(default=0, verbose_name='[필터링]②')),
                ('filtered_count_3', models.IntegerField(default=0, verbose_name='[필터링]③')),
                ('filtered_count_4', models.IntegerField(default=0, verbose_name='[필터링]④')),
                ('filtered_count_5', models.IntegerField(default=0, verbose_name='[필터링]⑤')),
                ('filtered_count_0', models.IntegerField(default=0, verbose_name='[필터링]미표기')),
                ('filtered_count_multiple', models.IntegerField(default=0, verbose_name='[필터링]중복표기')),
                ('filtered_count_sum', models.IntegerField(default=0, verbose_name='[필터링]총계')),
            ],
            options={
                'verbose_name': '[성적예측] 10_답안 개수(중위권)',
                'verbose_name_plural': '[성적예측] 10_답안 개수(중위권)',
                'db_table': 'a_prime_leet_predict_answer_count_mid_rank',
            },
        ),
        migrations.CreateModel(
            name='PredictAnswerCountTopRank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count_1', models.IntegerField(default=0, verbose_name='①')),
                ('count_2', models.IntegerField(default=0, verbose_name='②')),
                ('count_3', models.IntegerField(default=0, verbose_name='③')),
                ('count_4', models.IntegerField(default=0, verbose_name='④')),
                ('count_5', models.IntegerField(default=0, verbose_name='⑤')),
                ('count_0', models.IntegerField(default=0, verbose_name='미표기')),
                ('count_multiple', models.IntegerField(default=0, verbose_name='중복표기')),
                ('count_sum', models.IntegerField(default=0, verbose_name='총계')),
                ('answer_predict', models.GeneratedField(db_persist=True, expression=models.Case(models.When(models.Q(('count_1', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(1)), models.When(models.Q(('count_2', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(2)), models.When(models.Q(('count_3', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(3)), models.When(models.Q(('count_4', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(4)), models.When(models.Q(('count_5', django.db.models.functions.comparison.Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5'))), then=models.Value(5)), default=None), output_field=models.IntegerField())),
                ('filtered_count_1', models.IntegerField(default=0, verbose_name='[필터링]①')),
                ('filtered_count_2', models.IntegerField(default=0, verbose_name='[필터링]②')),
                ('filtered_count_3', models.IntegerField(default=0, verbose_name='[필터링]③')),
                ('filtered_count_4', models.IntegerField(default=0, verbose_name='[필터링]④')),
                ('filtered_count_5', models.IntegerField(default=0, verbose_name='[필터링]⑤')),
                ('filtered_count_0', models.IntegerField(default=0, verbose_name='[필터링]미표기')),
                ('filtered_count_multiple', models.IntegerField(default=0, verbose_name='[필터링]중복표기')),
                ('filtered_count_sum', models.IntegerField(default=0, verbose_name='[필터링]총계')),
            ],
            options={
                'verbose_name': '[성적예측] 09_답안 개수(상위권)',
                'verbose_name_plural': '[성적예측] 09_답안 개수(상위권)',
                'db_table': 'a_prime_leet_predict_answer_count_top_rank',
            },
        ),
        migrations.CreateModel(
            name='PredictRank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 등수')),
                ('subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 등수')),
                ('sum', models.IntegerField(blank=True, null=True, verbose_name='총점 등수')),
                ('participants', models.IntegerField(blank=True, null=True, verbose_name='총 인원')),
                ('filtered_subject_0', models.IntegerField(blank=True, null=True, verbose_name='[필터링]언어이해 등수')),
                ('filtered_subject_1', models.IntegerField(blank=True, null=True, verbose_name='[필터링]추리논증 등수')),
                ('filtered_sum', models.IntegerField(blank=True, null=True, verbose_name='[필터링]총점 등수')),
                ('filtered_participants', models.IntegerField(blank=True, null=True, verbose_name='[필터링]총 인원')),
            ],
            options={
                'verbose_name': '[성적예측] 06_등수(전체)',
                'verbose_name_plural': '[성적예측] 06_등수(전체)',
                'db_table': 'a_prime_leet_predict_rank',
            },
        ),
        migrations.CreateModel(
            name='PredictRankAspiration1',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 등수')),
                ('subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 등수')),
                ('sum', models.IntegerField(blank=True, null=True, verbose_name='총점 등수')),
                ('participants', models.IntegerField(blank=True, null=True, verbose_name='총 인원')),
                ('filtered_subject_0', models.IntegerField(blank=True, null=True, verbose_name='[필터링]언어이해 등수')),
                ('filtered_subject_1', models.IntegerField(blank=True, null=True, verbose_name='[필터링]추리논증 등수')),
                ('filtered_sum', models.IntegerField(blank=True, null=True, verbose_name='[필터링]총점 등수')),
                ('filtered_participants', models.IntegerField(blank=True, null=True, verbose_name='[필터링]총 인원')),
            ],
            options={
                'verbose_name': '[성적예측] 07_등수(1지망)',
                'verbose_name_plural': '[성적예측] 07_등수(1지망)',
                'db_table': 'a_prime_leet_predict_rank_aspiration_1',
            },
        ),
        migrations.CreateModel(
            name='PredictRankAspiration2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 등수')),
                ('subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 등수')),
                ('sum', models.IntegerField(blank=True, null=True, verbose_name='총점 등수')),
                ('participants', models.IntegerField(blank=True, null=True, verbose_name='총 인원')),
                ('filtered_subject_0', models.IntegerField(blank=True, null=True, verbose_name='[필터링]언어이해 등수')),
                ('filtered_subject_1', models.IntegerField(blank=True, null=True, verbose_name='[필터링]추리논증 등수')),
                ('filtered_sum', models.IntegerField(blank=True, null=True, verbose_name='[필터링]총점 등수')),
                ('filtered_participants', models.IntegerField(blank=True, null=True, verbose_name='[필터링]총 인원')),
            ],
            options={
                'verbose_name': '[성적예측] 08_등수(2지망)',
                'verbose_name_plural': '[성적예측] 08_등수(2지망)',
                'db_table': 'a_prime_leet_predict_rank_aspiration_2',
            },
        ),
        migrations.CreateModel(
            name='PredictScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 원점수')),
                ('raw_subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 원점수')),
                ('raw_sum', models.IntegerField(blank=True, null=True, verbose_name='총점 원점수')),
                ('subject_0', models.FloatField(blank=True, null=True, verbose_name='언어이해 표준점수')),
                ('subject_1', models.FloatField(blank=True, null=True, verbose_name='추리논증 표준점수')),
                ('sum', models.FloatField(blank=True, null=True, verbose_name='총점 표준점수')),
            ],
            options={
                'verbose_name': '[성적예측] 05_점수',
                'verbose_name_plural': '[성적예측] 05_점수',
                'db_table': 'a_prime_leet_predict_score',
            },
        ),
        migrations.CreateModel(
            name='PredictStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aspiration', models.CharField(choices=a_prime_leet.models.choices.statistics_aspiration_choice, default='전체', max_length=10, verbose_name='지망 대학')),
                ('raw_subject_0', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='언어이해 원점수')),
                ('raw_subject_1', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='추리논증 원점수')),
                ('raw_sum', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='총점 원점수')),
                ('subject_0', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='언어이해 표준점수')),
                ('subject_1', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='추리논증 표준점수')),
                ('sum', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='총점 표준점수')),
                ('filtered_raw_subject_0', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='[필터링]언어이해 원점수')),
                ('filtered_raw_subject_1', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='[필터링]추리논증 원점수')),
                ('filtered_raw_sum', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='[필터링]총점 원점수')),
                ('filtered_subject_0', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='[필터링]언어이해 표준점수')),
                ('filtered_subject_1', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='[필터링]추리논증 표준점수')),
                ('filtered_sum', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='[필터링]총점 표준점수')),
            ],
            options={
                'verbose_name': '[성적예측] 00_시험통계',
                'verbose_name_plural': '[성적예측] 00_시험통계',
                'db_table': 'a_prime_leet_predict_statistics',
            },
        ),
        migrations.CreateModel(
            name='PredictStudent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('serial', models.CharField(max_length=10, verbose_name='수험번호')),
                ('name', models.CharField(max_length=20, verbose_name='이름')),
                ('password', models.CharField(blank=True, max_length=10, null=True, verbose_name='비밀번호')),
                ('aspiration_1', models.CharField(blank=True, choices=a_prime_leet.models.choices.university_choice, max_length=10, null=True, verbose_name='1지망')),
                ('aspiration_2', models.CharField(blank=True, choices=a_prime_leet.models.choices.university_choice, max_length=10, null=True, verbose_name='2지망')),
                ('school', models.CharField(blank=True, choices=a_prime_leet.models.choices.university_choice, max_length=10, null=True, verbose_name='출신대학')),
                ('major', models.CharField(blank=True, choices=a_prime_leet.models.choices.major_choice, max_length=5, null=True, verbose_name='전공')),
                ('gpa_type', models.FloatField(blank=True, choices=a_prime_leet.models.choices.gpa_type_choice, null=True, verbose_name='학점(GPA) 종류')),
                ('gpa', models.FloatField(blank=True, null=True, verbose_name='학점(GPA)')),
                ('english_type', models.CharField(blank=True, choices=a_prime_leet.models.choices.english_type_choice, max_length=10, null=True, verbose_name='공인 영어성적 종류')),
                ('english', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='공인 영어성적')),
                ('is_filtered', models.BooleanField(default=False, verbose_name='필터링 여부')),
            ],
            options={
                'verbose_name': '[성적예측] 01_수험정보',
                'verbose_name_plural': '[성적예측] 01_수험정보',
                'db_table': 'a_prime_leet_predict_student',
            },
        ),
        migrations.AddField(
            model_name='resultanswer',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='작성 일시'),
            preserve_default=False,
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
        migrations.AddConstraint(
            model_name='resultstatistics',
            constraint=models.UniqueConstraint(fields=('leet', 'aspiration'), name='unique_prime_leet_result_statistics'),
        ),
        migrations.AddField(
            model_name='predictanswer',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answers', to='a_prime_leet.problem'),
        ),
        migrations.AddField(
            model_name='predictanswercount',
            name='problem',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answer_count', to='a_prime_leet.problem'),
        ),
        migrations.AddField(
            model_name='predictanswercountlowrank',
            name='problem',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answer_count_low_rank', to='a_prime_leet.problem'),
        ),
        migrations.AddField(
            model_name='predictanswercountmidrank',
            name='problem',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answer_count_mid_rank', to='a_prime_leet.problem'),
        ),
        migrations.AddField(
            model_name='predictanswercounttoprank',
            name='problem',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='predict_answer_count_top_rank', to='a_prime_leet.problem'),
        ),
        migrations.AddField(
            model_name='predictstatistics',
            name='leet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predict_statistics', to='a_prime_leet.leet'),
        ),
        migrations.AddField(
            model_name='predictstudent',
            name='leet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predict_students', to='a_prime_leet.leet'),
        ),
        migrations.AddField(
            model_name='predictstudent',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prime_leet_predict_students', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='predictscore',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='score', to='a_prime_leet.predictstudent'),
        ),
        migrations.AddField(
            model_name='predictrankaspiration2',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_aspiration_2', to='a_prime_leet.predictstudent'),
        ),
        migrations.AddField(
            model_name='predictrankaspiration1',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_aspiration_1', to='a_prime_leet.predictstudent'),
        ),
        migrations.AddField(
            model_name='predictrank',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank', to='a_prime_leet.predictstudent'),
        ),
        migrations.AddField(
            model_name='predictanswer',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='a_prime_leet.predictstudent'),
        ),
        migrations.AddConstraint(
            model_name='predictstatistics',
            constraint=models.UniqueConstraint(fields=('leet', 'aspiration'), name='unique_prime_leet_predict_statistics'),
        ),
        migrations.AddConstraint(
            model_name='predictstudent',
            constraint=models.UniqueConstraint(fields=('leet', 'user'), name='unique_prime_leet_predict_student'),
        ),
        migrations.AddConstraint(
            model_name='predictanswer',
            constraint=models.UniqueConstraint(fields=('student', 'problem'), name='unique_prime_leet_predict_answer'),
        ),
    ]
