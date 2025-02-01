from django.db import models
from django.db.models.functions import Greatest

from . import choices


def get_default_statistics():
    return {
        "participants": 0, "max": 0, "t10": 0, "t20": 0, "avg": 0
    }


class Statistics(models.Model):
    department = models.CharField(
        max_length=40, choices=choices.statistics_department_choice, default='전체', verbose_name='직렬')
    subject_0 = models.JSONField(default=get_default_statistics, verbose_name='헌법')
    subject_1 = models.JSONField(default=get_default_statistics, verbose_name='언어논리')
    subject_2 = models.JSONField(default=get_default_statistics, verbose_name='자료해석')
    subject_3 = models.JSONField(default=get_default_statistics, verbose_name='상황판단')
    average = models.JSONField(default=get_default_statistics, verbose_name='PSAT')

    class Meta:
        abstract = True


class ExtendedStatistics(Statistics):
    filtered_subject_0 = models.JSONField(default=get_default_statistics, verbose_name='[필터링]헌법')
    filtered_subject_1 = models.JSONField(default=get_default_statistics, verbose_name='[필터링]언어논리')
    filtered_subject_2 = models.JSONField(default=get_default_statistics, verbose_name='[필터링]자료해석')
    filtered_subject_3 = models.JSONField(default=get_default_statistics, verbose_name='[필터링]상황판단')
    filtered_average = models.JSONField(default=get_default_statistics, verbose_name='[필터링]PSAT')

    class Meta:
        abstract = True


class Student(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')
    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    password = models.CharField(max_length=10, default=0, verbose_name='비밀번호')

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
    answer_predict = models.GeneratedField(
        expression=models.Case(
            models.When(
                models.Q(count_1=Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5')),
                then=models.Value(1),
            ),
            models.When(
                models.Q(count_2=Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5')),
                then=models.Value(2),
            ),
            models.When(
                models.Q(count_3=Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5')),
                then=models.Value(3),
            ),
            models.When(
                models.Q(count_4=Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5')),
                then=models.Value(4),
            ),
            models.When(
                models.Q(count_5=Greatest('count_1', 'count_2', 'count_3', 'count_4', 'count_5')),
                then=models.Value(5),
            ),
            default=None,
        ),
        output_field=models.IntegerField(),
        db_persist=True,
    )

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

    def get_answer_predict_rate(self):
        if self.count_sum:
            return getattr(self, f'count_{self.answer_predict}') * 100 / self.count_sum


class ExtendedAnswerCount(AnswerCount):
    filtered_count_1 = models.IntegerField(default=0, verbose_name='[필터링]①')
    filtered_count_2 = models.IntegerField(default=0, verbose_name='[필터링]②')
    filtered_count_3 = models.IntegerField(default=0, verbose_name='[필터링]③')
    filtered_count_4 = models.IntegerField(default=0, verbose_name='[필터링]④')
    filtered_count_5 = models.IntegerField(default=0, verbose_name='[필터링]⑤')
    filtered_count_0 = models.IntegerField(default=0, verbose_name='[필터링]미표기')
    filtered_count_multiple = models.IntegerField(default=0, verbose_name='[필터링]중복표기')
    filtered_count_sum = models.IntegerField(default=0, verbose_name='[필터링]총계')

    class Meta:
        abstract = True


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


class ExtendedRank(Rank):
    filtered_subject_0 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]헌법')
    filtered_subject_1 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]언어논리')
    filtered_subject_2 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]자료해석')
    filtered_subject_3 = models.IntegerField(null=True, blank=True, verbose_name='[필터링]상황판단')
    filtered_average = models.IntegerField(null=True, blank=True, verbose_name='[필터링]PSAT')
    filtered_participants = models.IntegerField(null=True, blank=True, verbose_name='[필터링]총 인원')

    class Meta:
        abstract = True
