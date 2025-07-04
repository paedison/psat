from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone

from a_leet.models import abstract_models, Leet, Problem
from a_leet.models.queryset import predict_queryset as queryset
from common.models import User

verbose_name_prefix = '[합격예측] '


class PredictLeet(models.Model):
    leet = models.OneToOneField(Leet, on_delete=models.CASCADE, related_name='predict_leet')
    is_active = models.BooleanField(default=False, verbose_name='활성')
    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')
    predict_closed_at = models.DateTimeField(default=timezone.now, verbose_name='합격 에측 종료 일시')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_LEET'
        db_table = 'a_leet_predict_leet'
        ordering = ['-id']

    def __str__(self):
        return self.reference

    @property
    def year(self):
        return self.leet.year

    @property
    def exam(self):
        return self.leet.exam

    @property
    def reference(self):
        return f'{self.leet.year}{self.leet.exam}'

    @property
    def leet_info(self):
        return f'{self.leet.year}{self.leet.exam}'

    def is_not_page_opened(self):
        return timezone.now() <= self.page_opened_at

    def is_not_started(self):
        return self.page_opened_at < timezone.now() <= self.exam_started_at

    def is_started(self):
        return self.exam_started_at < timezone.now()

    def is_going_on(self):
        return self.exam_started_at < timezone.now() <= self.exam_finished_at

    def is_not_finished(self):
        return timezone.now() <= self.exam_finished_at

    def is_collecting_answer(self):
        return self.exam_finished_at < timezone.now() <= self.answer_predict_opened_at

    def is_answer_predict_opened(self):
        return self.answer_predict_opened_at < timezone.now() <= self.answer_official_opened_at

    def is_answer_official_opened(self):
        return self.answer_official_opened_at <= timezone.now()

    def is_predict_closed(self):
        return self.predict_closed_at <= timezone.now()


class PredictStatistics(abstract_models.ExtendedStatistics):
    objects = queryset.PredictStatisticsQuerySet.as_manager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='predict_statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_시험통계'
        db_table = 'a_leet_predict_statistics'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'aspiration'], name='unique_leet_predict_statistics')
        ]

    def __str__(self):
        return f'{self.leet.reference}-{self.aspiration}'


class PredictStudent(abstract_models.Student):
    objects = queryset.PredictStudentQuerySet.as_manager()
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='predict_students')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leet_predict_students')
    is_filtered = models.BooleanField(default=False, verbose_name='필터링 여부')
    answer_count = {'언어': 0, '추리': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_수험정보'
        db_table = 'a_leet_predict_student'
        constraints = [
            models.UniqueConstraint(fields=['leet', 'user'], name='unique_leet_predict_student')
        ]

    def __str__(self):
        return self.student_info

    def get_admin_detail_student_url(self):
        return reverse_lazy('leet:admin-detail-student', args=['predict', self.id])


class PredictAnswer(abstract_models.Answer):
    objects = queryset.PredictAnswerQuerySet.as_manager()
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')

    answer_student = answer_correct = None

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_답안'
        db_table = 'a_leet_predict_answer'
        constraints = [
            models.UniqueConstraint(fields=['student', 'problem'], name='unique_leet_predict_answer')
        ]

    def __str__(self):
        return f'{self.student.student_info}-{self.problem.reference}'


class PredictAnswerCount(abstract_models.ExtendedAnswerCount):
    objects = queryset.PredictAnswerCountQuerySet.as_manager()
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안 개수'
        db_table = 'a_leet_predict_answer_count'

    def __str__(self):
        return self.problem.reference


class PredictScore(abstract_models.Score):
    objects = queryset.PredictScoreQuerySet.as_manager()
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_점수'
        db_table = 'a_leet_predict_score'

    def __str__(self):
        return self.student.student_info


class PredictRank(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_등수(전체)'
        db_table = 'a_leet_predict_rank'

    def __str__(self):
        return self.student.student_info


class PredictRankAspiration1(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_aspiration_1')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_등수(1지망)'
        db_table = 'a_leet_predict_rank_aspiration_1'

    def __str__(self):
        return self.student.student_info


class PredictRankAspiration2(abstract_models.ExtendedRank):
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='rank_aspiration_2')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_등수(2지망)'
        db_table = 'a_leet_predict_rank_aspiration_2'

    def __str__(self):
        return self.student.student_info


class PredictAnswerCountTopRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(상위권)'
        db_table = 'a_leet_predict_answer_count_top_rank'

    def __str__(self):
        return self.problem.reference


class PredictAnswerCountMidRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(중위권)'
        db_table = 'a_leet_predict_answer_count_mid_rank'

    def __str__(self):
        return self.problem.reference


class PredictAnswerCountLowRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(Problem, on_delete=models.CASCADE, related_name='predict_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(하위권)'
        db_table = 'a_leet_predict_answer_count_low_rank'

    def __str__(self):
        return self.problem.reference
