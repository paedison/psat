from django.urls import reverse_lazy
from django.utils import timezone
from django.db import models

from common.models import User
from .problem_models import Psat, Problem
from . import choices, abstract_models, managers

verbose_name_prefix = '[합격예측] '


class PredictPsat(models.Model):
    psat = models.OneToOneField(Psat, on_delete=models.CASCADE, related_name='predict_psat')
    is_active = models.BooleanField(default=False, verbose_name='활성')
    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')
    predict_closed_at = models.DateTimeField(default=timezone.now, verbose_name='합격 에측 종료 일시')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}00_PSAT'
        db_table = 'a_psat_predict_psat'
        ordering = ['-id']

    def __str__(self):
        return f'[PSAT]PredictPsat(#{self.id}):{self.reference}'

    @property
    def year(self):
        return self.psat.year

    @property
    def exam(self):
        return self.psat.exam

    @property
    def reference(self):
        return f'{self.psat.year}{self.psat.exam}'

    @property
    def psat_info(self):
        return f'{self.psat.year}{self.psat.exam}'

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

    @property
    def exam_abbr(self):
        exam_dict = {
            '행시': '5급공채 등',
            '입시': '입법고시',
            '칠급': '7급공채 등',
        }
        return exam_dict[self.psat.exam]


class PredictCategory(models.Model):
    objects = managers.CategoryManager()
    exam = models.CharField(
        max_length=2, choices=choices.predict_exam_choice, default='행시', verbose_name='시험')
    unit = models.CharField(
        max_length=20, choices=choices.predict_unit_choice, default='5급 행정', verbose_name='모집단위')
    department = models.CharField(
        max_length=40, choices=choices.predict_department_choice, default='일반행정', verbose_name='직렬')
    order = models.SmallIntegerField(default=1, verbose_name='순서')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}01_모집단위 및 직렬'
        db_table = 'a_psat_predict_category'
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'unit', 'department'], name='unique_psat_predict_category'
            ),
        ]


class PredictStatistics(abstract_models.ExtendedStatistics):
    objects = managers.StatisticsManager()
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_statistics')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}02_시험통계'
        db_table = 'a_psat_predict_statistics'
        constraints = [
            models.UniqueConstraint(
                fields=['psat', 'department'], name='unique_psat_predict_statistics'
            ),
        ]

    def __str__(self):
        return f'[PSAT]PredictStatistics(#{self.id}):{self.psat.reference}'

    @property
    def psat_info(self):
        return f'{self.psat.year}{self.psat.exam}'


class PredictStudent(abstract_models.Student):
    objects = managers.StudentManager()
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='predict_students')
    category = models.ForeignKey(
        PredictCategory, on_delete=models.CASCADE, related_name='predict_students')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_predict_students')
    is_filtered = models.BooleanField(default=False, verbose_name='필터링 여부')
    prime_id = models.CharField(max_length=15, null=True, blank=True, verbose_name='프라임법학원 ID')
    department = ''
    answer_count = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0, '평균': 0}

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}03_수험정보'
        db_table = 'a_psat_predict_student'
        constraints = [models.UniqueConstraint(fields=['psat', 'user'], name='unique_psat_predict_student')]

    def __str__(self):
        return f'[PSAT]PredictStudent(#{self.id}):{self.psat.reference}({self.student_info})'

    @property
    def psat_info(self):
        return f'{self.psat.year}{self.psat.exam}'

    def get_admin_predict_student_detail_url(self):
        return reverse_lazy('psat:admin-predict-student-detail', args=[self.id])


class PredictAnswer(abstract_models.Answer):
    objects = managers.AnswerManager()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성 일시')
    student = models.ForeignKey(PredictStudent, on_delete=models.CASCADE, related_name='answers')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='predict_answers')

    answer_student = answer_correct = None

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}04_답안'
        db_table = 'a_psat_predict_answer'
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'problem'], name='unique_psat_predict_answer'
            )
        ]

    def __str__(self):
        return f'[PSAT]PredictAnswer(#{self.id}):{self.student.student_info}-{self.problem.reference}'

    @property
    def problem_info(self):
        return self.problem.reference

    @property
    def student_info(self):
        return self.student.student_info

    @property
    def answer_official(self):
        return self.problem.answer


class PredictAnswerCount(abstract_models.ExtendedAnswerCount):
    objects = managers.AnswerCountManager()
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='predict_answer_count')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}05_답안 개수'
        db_table = 'a_psat_predict_answer_count'

    def __str__(self):
        return f'[PSAT]PredictAnswerCount(#{self.id}):{self.problem.reference}'

    @property
    def problem_info(self):
        return self.problem.reference


class PredictScore(abstract_models.Score):
    objects = managers.ScoreManager()
    student = models.OneToOneField(PredictStudent, on_delete=models.CASCADE, related_name='score')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}06_점수'
        db_table = 'a_psat_predict_score'

    def __str__(self):
        return f'[PSAT]PredictScore(#{self.id}):{self.student.student_info}'

    @property
    def psat_info(self):
        return self.student.psat_info


class PredictRankTotal(abstract_models.ExtendedRank):
    student = models.OneToOneField(
        PredictStudent, on_delete=models.CASCADE, related_name='rank_total')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}07_전체 등수'
        db_table = 'a_psat_predict_rank_total'

    def __str__(self):
        return f'[PSAT]PredictRankTotal(#{self.id}):{self.student.student_info}'

    @property
    def psat_info(self):
        return self.student.psat_info


class PredictRankCategory(abstract_models.ExtendedRank):
    student = models.OneToOneField(
        PredictStudent, on_delete=models.CASCADE, related_name='rank_category')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}08_직렬 등수'
        db_table = 'a_psat_predict_rank_category'

    def __str__(self):
        return f'[PSAT]PredictRankCategory(#{self.id}):{self.student.student_info}'

    @property
    def psat_info(self):
        return self.student.psat_info


class PredictAnswerCountTopRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='predict_answer_count_top_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}09_답안 개수(상위권)'
        db_table = 'a_psat_predict_answer_count_top_rank'

    def __str__(self):
        return f'[PSAT]PredictAnswerCountTopRank(#{self.id}):{self.problem.reference}'

    @property
    def problem_info(self):
        return self.problem.reference


class PredictAnswerCountMidRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='predict_answer_count_mid_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}10_답안 개수(중위권)'
        db_table = 'a_psat_predict_answer_count_mid_rank'

    def __str__(self):
        return f'[PSAT]PredictAnswerCountMidRank(#{self.id}):{self.problem.reference}'

    @property
    def problem_info(self):
        return self.problem.reference


class PredictAnswerCountLowRank(abstract_models.ExtendedAnswerCount):
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, related_name='predict_answer_count_low_rank')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}11_답안 개수(하위권)'
        db_table = 'a_psat_predict_answer_count_low_rank'

    def __str__(self):
        return f'[PSAT]PredictAnswerCountLowRank(#{self.id}):{self.problem.reference}'

    @property
    def problem_info(self):
        return self.problem.reference


class PredictLocation(models.Model):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='locations')
    category = models.ForeignKey(
        PredictCategory, on_delete=models.CASCADE, verbose_name='모집단위·직렬', related_name='locations')
    serial_start = models.IntegerField(verbose_name='시작 수험번호')
    serial_end = models.IntegerField(verbose_name='마지막 수험번호')
    region = models.CharField(max_length=10, verbose_name='지역')
    school = models.CharField(max_length=30, verbose_name='학교명')
    address = models.CharField(max_length=50, verbose_name='주소')
    contact = models.CharField(max_length=20, blank=True, null=True, verbose_name='연락처')

    class Meta:
        verbose_name = verbose_name_plural = f'{verbose_name_prefix}12_시험 장소'
        db_table = 'a_psat_predict_location'

    @property
    def psat_info(self):
        return f'{self.psat.year}{self.psat.exam}'
