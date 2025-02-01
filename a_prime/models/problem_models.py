from datetime import datetime, timedelta
from django.utils import timezone

from django.db import models
from django.urls import reverse_lazy

from . import choices


class Psat(models.Model):
    year = models.IntegerField(
        choices=choices.year_choice, default=datetime.now().year, verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=choices.exam_choice, default='프모', verbose_name='시험')
    round = models.IntegerField(choices=choices.round_choice, verbose_name='회차')
    is_active = models.BooleanField(default=False, verbose_name='활성')

    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(
        default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(
        default=timezone.now, verbose_name='공식 정답 공개 일시')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임] 00_PSAT 모의고사"
        ordering = ['-year', 'round']
        constraints = [
            models.UniqueConstraint(fields=['year', 'exam', 'round'], name='unique_prime_psat'),
        ]

    def __str__(self):
        return f'[Prime]Psat(#{self.id}):{self.reference}'

    @property
    def score_opened_at(self):
        score_open_date = self.answer_official_opened_at + timedelta(days=5)
        return score_open_date.replace(hour=8, minute=0)

    @property
    def reference(self):
        return f'{self.year}-{self.round}'

    @property
    def full_reference(self):
        return ' '.join([self.get_year_display(), self.get_exam_display()])

    @property
    def is_not_page_opened(self):
        return timezone.now() <= self.page_opened_at

    @property
    def is_not_started(self):
        return self.page_opened_at < timezone.now() <= self.exam_started_at

    @property
    def is_started(self):
        return self.exam_started_at < timezone.now()

    @property
    def is_going_on(self):
        return self.exam_started_at < timezone.now() <= self.exam_finished_at

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
    def is_predict_closed(self):
        return self.score_opened_at <= timezone.now()

    @staticmethod
    def get_admin_list_url():
        return reverse_lazy('prime:admin-list')

    def get_admin_predict_detail_url(self):
        return reverse_lazy('prime:admin-detail', args=['predict', self.id])

    def get_admin_result_detail_url(self):
        return reverse_lazy('prime:admin-detail', args=['result', self.id])

    def get_admin_update_url(self):
        return reverse_lazy('prime:admin-update', args=[self.id])

    @staticmethod
    def get_result_list_url():
        return reverse_lazy('prime:result-list')

    def get_result_detail_url(self):
        return reverse_lazy('prime:result-detail', args=[self.id])

    def get_result_register_url(self):
        return reverse_lazy('prime:result-register', args=[self.id])

    def get_result_unregister_url(self):
        return reverse_lazy('prime:result-unregister', args=[self.id])

    def get_result_print_url(self):
        return reverse_lazy('prime:result-print', args=[self.id])

    def get_result_modal_url(self):
        return reverse_lazy('prime:result-modal', args=[self.id])

    @staticmethod
    def get_predict_list_url():
        return reverse_lazy('prime:predict-list')

    def get_predict_detail_url(self):
        return reverse_lazy('prime:predict-detail', args=[self.id])

    def get_predict_register_url(self):
        return reverse_lazy('prime:predict-register', args=[self.id])

    def get_predict_answer_input_url(self, subject_field):
        return reverse_lazy('prime:predict-answer-input', args=[self.id, subject_field])

    def get_predict_answer_confirm_url(self, subject_field):
        return reverse_lazy('prime:predict-answer-confirm', args=[self.id, subject_field])

    def get_predict_unregister_url(self):
        return reverse_lazy('prime:predict-unregister', args=[self.id])

    def get_predict_modal_url(self):
        return reverse_lazy('prime:predict-modal', args=[self.id])


class Problem(models.Model):
    psat = models.ForeignKey(
        Psat, on_delete=models.CASCADE, related_name='problems', verbose_name='PSAT')
    subject = models.CharField(
        max_length=2, choices=choices.subject_choice, default='언어', verbose_name='과목')
    number = models.IntegerField(choices=choices.number_choice, default=1, verbose_name='번호')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='정답')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임] 01_문제"
        ordering = ['psat', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['psat', 'subject', 'number'], name='unique_prime_problem'
            ),
        ]

    def __str__(self):
        return f'[Prime]Problem(#{self.id}):{self.reference}'

    @property
    def year_ex_sub(self):
        return f'{self.psat.year}{self.psat.exam}{self.subject}'

    @property
    def _reference(self):
        return f'{self.psat.year}{self.psat.exam[0]}{self.subject[0]}'

    @property
    def reference(self):
        return f'{self._reference}-{self.number:02}'

    @property
    def year_exam_subject(self):
        return ' '.join([
            self.psat.get_year_display(), self.psat.get_exam_display(), self.get_subject_display()
        ])

    @property
    def full_reference(self):
        return ' '.join([self.year_exam_subject, self.get_number_display()])

    def get_absolute_url(self):
        return reverse_lazy('psat:problem-detail', args=[self.id])

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_psat_problem_change', args=[self.id])


class Category(models.Model):
    exam = models.CharField(
        max_length=2, choices=choices.exam_choice, default='프모', verbose_name='시험')
    unit = models.CharField(
        max_length=20, choices=choices.unit_choice, default='5급 행정', verbose_name='모집단위')
    department = models.CharField(
        max_length=40, choices=choices.department_choice, default='5급 일반행정', verbose_name='직렬')
    order = models.SmallIntegerField(default=1, verbose_name='순서')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임] 03_모집단위 및 직렬"
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'unit', 'department'], name='unique_prime_category'
            ),
        ]

    def __str__(self):
        return f'[Prime]Category(#{self.id}):{self.unit}-{self.department}'
