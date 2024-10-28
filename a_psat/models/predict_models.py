from django.utils import timezone
from django.db import models

from common.models import User
from .problem_models import Psat, Problem
from . import choices


class PredictPsat(models.Model):
    psat = models.OneToOneField(Psat, on_delete=models.CASCADE, related_name='predict_psat')
    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 00_PSAT"
        db_table = 'a_psat_predict_psat'

    def __str__(self):
        return f'[PSAT]PredictPsat(#{self.id}):{self.exam_reference}'

    @property
    def exam_reference(self): return f'{self.psat.year}{self.psat.exam}'

    @property
    def is_not_page_opened(self):
        return timezone.now() <= self.page_opened_at

    @property
    def is_not_finished(self):
        return timezone.now() <= self.exam_finished_at

    @property
    def is_collecting_answer(self):
        return self.exam_finished_at < timezone.now() <= self.answer_predict_opened_at

    @property
    def is_answer_predict_opened(self):
        return self.answer_predict_opened_at < timezone.now() <= self.answer_official_opened_at

    @property
    def is_answer_official_opened(self):
        return self.answer_official_opened_at <= timezone.now()

    @property
    def exam_abbr(self):
        exam_dict = {
            '행시': '5급공채 등',
            '입시': '입법고시',
            '칠급': '7급공채 등',
        }
        return exam_dict[self.psat.exam]


class PredictCategory(models.Model):
    exam = models.CharField(max_length=2, choices=choices.predict_exam_choice, default='행시', verbose_name='시험')
    unit = models.CharField(max_length=20, choices=choices.predict_unit_choice, default='5급 행정', verbose_name='모집단위')
    department = models.CharField(max_length=40, default='일반행정', verbose_name='직렬')
    order = models.SmallIntegerField(default=1, verbose_name='순서')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 01_모집단위 및 직렬"
        db_table = 'a_psat_predict_category'


class PredictStudent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_predict_students')
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_students')
    category = models.ForeignKey(PredictCategory, on_delete=models.CASCADE, related_name='students')

    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 02_수험정보"
        db_table = 'a_psat_predict_student'


class PredictAnswer(models.Model):
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='답안')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 03_답안"
        db_table = 'a_psat_predict_answer'


class PredictAnswerCount(models.Model):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_counts')
    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_5 = models.IntegerField(default=0, verbose_name='⑤')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_total = models.IntegerField(default=0, verbose_name='총계')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 04_답안 개수"
        db_table = 'a_psat_predict_answer_count'


class PredictScore(models.Model):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='상황판단')
    total = models.FloatField(null=True, blank=True, verbose_name='PSAT 총점')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 05_점수"
        db_table = 'a_psat_predict_score'


class PredictRankTotal(models.Model):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_totals')
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='상황판단')
    total = models.FloatField(null=True, blank=True, verbose_name='PSAT')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 06_전체 등수"
        db_table = 'a_psat_predict_rank_total'


class PredictRankCategory(models.Model):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_categories')
    subject_0 = models.FloatField(null=True, blank=True, verbose_name='헌법')
    subject_1 = models.FloatField(null=True, blank=True, verbose_name='언어논리')
    subject_2 = models.FloatField(null=True, blank=True, verbose_name='자료해석')
    subject_3 = models.FloatField(null=True, blank=True, verbose_name='상황판단')
    total = models.FloatField(null=True, blank=True, verbose_name='PSAT')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 07_직렬 등수"
        db_table = 'a_psat_predict_rank_category'


class PredictLocation(models.Model):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_locations')
    category = models.ForeignKey(PredictCategory, on_delete=models.CASCADE, verbose_name='모집단위·직렬')
    serial_start = models.IntegerField(verbose_name='시작 수험번호')
    serial_end = models.IntegerField(verbose_name='마지막 수험번호')
    region = models.CharField(max_length=10, verbose_name='지역')
    school = models.CharField(max_length=30, verbose_name='학교명')
    address = models.CharField(max_length=50, verbose_name='주소')
    contact = models.CharField(max_length=20, blank=True, null=True, verbose_name='연락처')

    class Meta:
        verbose_name = verbose_name_plural = "[합격예측] 08_시험 장소"
        db_table = 'a_psat_predict_location'
