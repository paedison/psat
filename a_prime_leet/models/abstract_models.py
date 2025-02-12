from django.db import models

from . import choices


def get_default_statistics():
    return {
        "participants": 0, "max": 0, "t10": 0, "t25": 0, "t50": 0, "avg": 0
    }


class ResultStatistics(models.Model):
    aspiration = models.CharField(
        max_length=10, choices=choices.statistics_aspiration_choice, default='전체', verbose_name='지망 대학')
    raw_subject_0 = models.JSONField(default=get_default_statistics, verbose_name='언어이해 원점수')
    raw_subject_1 = models.JSONField(default=get_default_statistics, verbose_name='추리논증 원점수')
    raw_sum = models.JSONField(default=get_default_statistics, verbose_name='총점 원점수')
    subject_0 = models.JSONField(default=get_default_statistics, verbose_name='언어이해 표준점수')
    subject_1 = models.JSONField(default=get_default_statistics, verbose_name='추리논증 표준점수')
    sum = models.JSONField(default=get_default_statistics, verbose_name='총점 표준점수')

    class Meta:
        abstract = True


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    name = models.CharField(max_length=20, verbose_name='이름')
    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')
    aspiration_1 = models.CharField(
        max_length=10, choices=choices.university_choice, null=True, blank=True, verbose_name='1지망')
    aspiration_2 = models.CharField(
        max_length=10, choices=choices.university_choice, null=True, blank=True, verbose_name='2지망')
    school = models.CharField(
        max_length=10, choices=choices.university_choice, null=True, blank=True, verbose_name='출신대학')
    major = models.CharField(
        max_length=5, choices=choices.major_choice, null=True, blank=True, verbose_name='전공')
    gpa_type = models.FloatField(
        choices=choices.gpa_type_choice, null=True, blank=True, verbose_name='학점(GPA) 종류')
    gpa = models.FloatField(null=True, blank=True, verbose_name='학점(GPA)')
    english_type = models.CharField(
        max_length=10, choices=choices.english_type_choice, null=True, blank=True, verbose_name='공인 영어성적 종류')
    english = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='공인 영어성적')

    class Meta:
        abstract = True

    @property
    def student_info(self):
        return f'{self.serial}-{self.name}'


class Answer(models.Model):
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='답안')

    class Meta:
        abstract = True


class AnswerCount(models.Model):
    problem = None
    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_5 = models.IntegerField(default=0, verbose_name='⑤')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_sum = models.IntegerField(default=0, verbose_name='총계')

    class Meta:
        abstract = True

    def get_answer_rate(self, ans: int):
        if self.count_sum:
            if 1 <= self.problem.answer <= 5:
                count_target = getattr(self, f'count_{ans}')
            else:
                answer_official_list = [int(digit) for digit in str(self.problem.answer)]
                count_target = sum(
                    getattr(self, f'count_{ans_official}') for ans_official in answer_official_list
                )
            return count_target * 100 / self.count_sum


class Score(models.Model):
    raw_subject_0 = models.IntegerField(null=True, blank=True, verbose_name='언어이해 원점수')
    raw_subject_1 = models.IntegerField(null=True, blank=True, verbose_name='추리논증 원점수')
    raw_sum = models.IntegerField(null=True, blank=True, verbose_name='총점 원점수')
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='언어이해 표준점수')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='추리논증 표준점수')
    sum = models.FloatField(null=True, blank=True, verbose_name='총점 표준점수')

    class Meta:
        abstract = True


class Rank(models.Model):
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='언어이해 등수')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='추리논증 등수')
    sum = models.IntegerField(null=True, blank=True, verbose_name='총점 등수')
    participants = models.IntegerField(null=True, blank=True, verbose_name='총 인원')

    class Meta:
        abstract = True

    def get_rank_raio(self, rank_code: str):
        _rank = getattr(self, rank_code)
        if self.participants:
            return _rank / self.participants

