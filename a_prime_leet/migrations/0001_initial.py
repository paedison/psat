# Generated by Django 5.1 on 2025-02-12 02:50

import a_prime_leet.models.abstract_models
import a_prime_leet.models.choices
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
            name='Leet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(choices=a_prime_leet.models.choices.year_choice, default=2026, verbose_name='연도')),
                ('exam', models.CharField(choices=a_prime_leet.models.choices.exam_choice, default='프모', max_length=2, verbose_name='시험')),
                ('round', models.IntegerField(choices=a_prime_leet.models.choices.round_choice, verbose_name='회차')),
                ('name', models.CharField(max_length=30, verbose_name='시험명')),
                ('abbr', models.CharField(max_length=30, verbose_name='약칭')),
                ('is_active', models.BooleanField(default=False, verbose_name='활성')),
                ('page_opened_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='페이지 오픈 일시')),
                ('exam_started_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='시험 시작 일시')),
                ('exam_finished_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='시험 종료 일시')),
                ('answer_predict_opened_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='예상 정답 공개 일시')),
                ('answer_official_opened_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='공식 정답 공개 일시')),
            ],
            options={
                'verbose_name': '[프라임LEET] 00_LEET 모의고사',
                'verbose_name_plural': '[프라임LEET] 00_LEET 모의고사',
                'ordering': ['-id'],
                'constraints': [models.UniqueConstraint(fields=('year', 'exam', 'name'), name='unique_prime_leet_leet')],
            },
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(choices=a_prime_leet.models.choices.subject_choice, default='언어', max_length=2, verbose_name='과목')),
                ('number', models.IntegerField(choices=a_prime_leet.models.choices.number_choice, default=1, verbose_name='번호')),
                ('answer', models.IntegerField(choices=a_prime_leet.models.choices.answer_choice, default=1, verbose_name='정답')),
                ('leet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems', to='a_prime_leet.leet', verbose_name='Leet')),
            ],
            options={
                'verbose_name': '[프라임LEET] 01_문제',
                'verbose_name_plural': '[프라임LEET] 01_문제',
                'ordering': ['leet', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ResultAnswerCount',
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
                ('problem', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result_answer_count', to='a_prime_leet.problem')),
            ],
            options={
                'verbose_name': '[성적확인] 04_답안 개수',
                'verbose_name_plural': '[성적확인] 04_답안 개수',
                'db_table': 'a_prime_leet_result_answer_count',
            },
        ),
        migrations.CreateModel(
            name='ResultAnswerCountLowRank',
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
                ('problem', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result_answer_count_low_rank', to='a_prime_leet.problem')),
            ],
            options={
                'verbose_name': '[성적확인] 11_답안 개수(하위권)',
                'verbose_name_plural': '[성적확인] 11_답안 개수(하위권)',
                'db_table': 'a_prime_leet_result_answer_count_low_rank',
            },
        ),
        migrations.CreateModel(
            name='ResultAnswerCountMidRank',
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
                ('problem', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result_answer_count_mid_rank', to='a_prime_leet.problem')),
            ],
            options={
                'verbose_name': '[성적확인] 10_답안 개수(중위권)',
                'verbose_name_plural': '[성적확인] 10_답안 개수(중위권)',
                'db_table': 'a_prime_leet_result_answer_count_mid_rank',
            },
        ),
        migrations.CreateModel(
            name='ResultAnswerCountTopRank',
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
                ('problem', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result_answer_count_top_rank', to='a_prime_leet.problem')),
            ],
            options={
                'verbose_name': '[성적확인] 09_답안 개수(상위권)',
                'verbose_name_plural': '[성적확인] 09_답안 개수(상위권)',
                'db_table': 'a_prime_leet_result_answer_count_top_rank',
            },
        ),
        migrations.CreateModel(
            name='ResultStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aspiration', models.CharField(choices=a_prime_leet.models.choices.statistics_aspiration_choice, default='전체', max_length=10, verbose_name='지망 대학')),
                ('raw_subject_0', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='언어이해 원점수')),
                ('raw_subject_1', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='추리논증 원점수')),
                ('raw_sum', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='총점 원점수')),
                ('subject_0', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='언어이해 표준점수')),
                ('subject_1', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='추리논증 표준점수')),
                ('sum', models.JSONField(default=a_prime_leet.models.abstract_models.get_default_statistics, verbose_name='총점 표준점수')),
                ('leet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='result_statistics', to='a_prime_leet.leet')),
            ],
            options={
                'verbose_name': '[성적확인] 00_시험통계',
                'verbose_name_plural': '[성적확인] 00_시험통계',
                'db_table': 'a_prime_leet_result_statistics',
            },
        ),
        migrations.CreateModel(
            name='ResultStudent',
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
                ('leet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='result_students', to='a_prime_leet.leet')),
            ],
            options={
                'verbose_name': '[성적확인] 01_수험정보',
                'verbose_name_plural': '[성적확인] 01_수험정보',
                'db_table': 'a_prime_leet_result_student',
            },
        ),
        migrations.CreateModel(
            name='ResultScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 원점수')),
                ('raw_subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 원점수')),
                ('raw_sum', models.IntegerField(blank=True, null=True, verbose_name='총점 원점수')),
                ('subject_0', models.FloatField(blank=True, null=True, verbose_name='언어이해 표준점수')),
                ('subject_1', models.FloatField(blank=True, null=True, verbose_name='추리논증 표준점수')),
                ('sum', models.FloatField(blank=True, null=True, verbose_name='총점 표준점수')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='score', to='a_prime_leet.resultstudent')),
            ],
            options={
                'verbose_name': '[성적확인] 05_점수',
                'verbose_name_plural': '[성적확인] 05_점수',
                'db_table': 'a_prime_leet_result_score',
            },
        ),
        migrations.CreateModel(
            name='ResultRegistry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prime_leet_result_registries', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registries', to='a_prime_leet.resultstudent')),
            ],
            options={
                'verbose_name': '[성적확인] 02_수험정보 연결',
                'verbose_name_plural': '[성적확인] 02_수험정보 연결',
                'db_table': 'a_prime_leet_result_registry',
            },
        ),
        migrations.CreateModel(
            name='ResultRankAspiration2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 등수')),
                ('subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 등수')),
                ('sum', models.IntegerField(blank=True, null=True, verbose_name='총점 등수')),
                ('participants', models.IntegerField(blank=True, null=True, verbose_name='총 인원')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_aspiration_2', to='a_prime_leet.resultstudent')),
            ],
            options={
                'verbose_name': '[성적확인] 08_등수(2지망)',
                'verbose_name_plural': '[성적확인] 08_등수(2지망)',
                'db_table': 'a_prime_leet_result_rank_aspiration_2',
            },
        ),
        migrations.CreateModel(
            name='ResultRankAspiration1',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 등수')),
                ('subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 등수')),
                ('sum', models.IntegerField(blank=True, null=True, verbose_name='총점 등수')),
                ('participants', models.IntegerField(blank=True, null=True, verbose_name='총 인원')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank_aspiration_1', to='a_prime_leet.resultstudent')),
            ],
            options={
                'verbose_name': '[성적확인] 07_등수(1지망)',
                'verbose_name_plural': '[성적확인] 07_등수(1지망)',
                'db_table': 'a_prime_leet_result_rank_aspiration_1',
            },
        ),
        migrations.CreateModel(
            name='ResultRank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_0', models.IntegerField(blank=True, null=True, verbose_name='언어이해 등수')),
                ('subject_1', models.IntegerField(blank=True, null=True, verbose_name='추리논증 등수')),
                ('sum', models.IntegerField(blank=True, null=True, verbose_name='총점 등수')),
                ('participants', models.IntegerField(blank=True, null=True, verbose_name='총 인원')),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rank', to='a_prime_leet.resultstudent')),
            ],
            options={
                'verbose_name': '[성적확인] 06_등수(전체)',
                'verbose_name_plural': '[성적확인] 06_등수(전체)',
                'db_table': 'a_prime_leet_result_rank',
            },
        ),
        migrations.CreateModel(
            name='ResultAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.IntegerField(choices=a_prime_leet.models.choices.answer_choice, default=1, verbose_name='답안')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='result_answers', to='a_prime_leet.problem')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='a_prime_leet.resultstudent')),
            ],
            options={
                'verbose_name': '[성적확인] 03_답안',
                'verbose_name_plural': '[성적확인] 03_답안',
                'db_table': 'a_prime_leet_result_answer',
            },
        ),
        migrations.AddConstraint(
            model_name='problem',
            constraint=models.UniqueConstraint(fields=('leet', 'subject', 'number'), name='unique_prime_leet_problem'),
        ),
        migrations.AddConstraint(
            model_name='resultstudent',
            constraint=models.UniqueConstraint(fields=('leet', 'name', 'serial'), name='unique_prime_leet_result_student'),
        ),
        migrations.AddConstraint(
            model_name='resultregistry',
            constraint=models.UniqueConstraint(fields=('user', 'student'), name='unique_prime_leet_result_registry'),
        ),
        migrations.AddConstraint(
            model_name='resultanswer',
            constraint=models.UniqueConstraint(fields=('student', 'problem'), name='unique_prime_leet_result_answer'),
        ),
    ]
