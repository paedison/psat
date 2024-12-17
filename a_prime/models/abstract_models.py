from django.db import models

from . import choices


class ResultStatistics(models.Model):
    department = models.CharField(
        max_length=40, choices=choices.statistics_department_choices, default='전체', verbose_name='직렬')
    subject_0 = models.JSONField(default=dict, verbose_name='헌법')
    subject_1 = models.JSONField(default=dict, verbose_name='언어논리')
    subject_2 = models.JSONField(default=dict, verbose_name='자료해석')
    subject_3 = models.JSONField(default=dict, verbose_name='상황판단')
    average = models.JSONField(default=dict, verbose_name='PSAT')

    class Meta:
        abstract = True


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')

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
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='상황판단')
    sum = models.FloatField(null=True, blank=True, verbose_name='PSAT 총점')
    average = models.FloatField(null=True, blank=True, verbose_name='PSAT 평균')

    class Meta:
        abstract = True


class Rank(models.Model):
    subject_0 = models.IntegerField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.IntegerField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.IntegerField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.IntegerField(null=True, blank=True, verbose_name='상황판단')
    average = models.IntegerField(null=True, blank=True, verbose_name='PSAT')
    participants = models.IntegerField(null=True, blank=True, verbose_name='총 인원')

    class Meta:
        abstract = True

    def get_rank_raio(self, rank_code: str):
        _rank = getattr(self, rank_code)
        if self.participants:
            return _rank / self.participants

