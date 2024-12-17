from datetime import datetime
from django.utils import timezone

from django.db import models
from django.urls import reverse_lazy

from . import choices


class Psat(models.Model):
    year = models.IntegerField(choices=choices.year_choice, default=datetime.now().year, verbose_name='연도')
    exam = models.CharField(max_length=2, choices=choices.exam_choice, default='프모', verbose_name='시험')
    round = models.IntegerField(choices=choices.round_choice, verbose_name='회차')
    is_active = models.BooleanField(default=False, verbose_name='활성')

    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임] 00_PSAT 모의고사"
        ordering = ['-year', 'round']
        constraints = [
            models.UniqueConstraint(fields=['year', 'exam', 'round'], name='unique_prime_psat'),
        ]

    def __str__(self):
        return f'[Prime]Psat(#{self.id}):{self.reference}'

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

    @staticmethod
    def get_admin_list_url():
        return reverse_lazy('prime:score-admin-list')

    def get_admin_detail_url(self):
        return reverse_lazy('prime:score-admin-detail', args=[self.id])

    def get_admin_update_url(self):
        return reverse_lazy('prime:score-admin-update', args=[self.id])

    def get_admin_problem_list_url(self):
        return reverse_lazy('psat:admin-problem-list', args=[self.id])

    def get_admin_psat_active_url(self):
        return reverse_lazy('psat:admin-psat-active', args=[self.id])

    @staticmethod
    def get_score_list_url():
        return reverse_lazy('prime:score-list')

    def get_score_detail_url(self):
        return reverse_lazy('prime:score-detail', args=[self.id])

    def get_score_register_url(self):
        return reverse_lazy('prime:score-register', args=[self.id])

    def get_score_unregister_url(self):
        return reverse_lazy('prime:score-unregister', args=[self.id])

    def get_score_print_url(self):
        return reverse_lazy('prime:score-print', args=[self.id])

    def get_score_modal_url(self):
        return reverse_lazy('prime:score-modal', args=[self.id])


class Problem(models.Model):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='problems', verbose_name='PSAT')
    subject = models.CharField(max_length=2, choices=choices.subject_choice, default='언어', verbose_name='과목')
    number = models.IntegerField(choices=choices.number_choice, default=1, verbose_name='번호')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='정답')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임] 01_문제"
        ordering = ['psat', 'id']
        constraints = [
            models.UniqueConstraint(fields=['psat', 'subject', 'number'], name='unique_prime_problem'),
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
        return ' '.join([self.psat.get_year_display(), self.psat.get_exam_display(), self.get_subject_display()])

    @property
    def full_reference(self):
        return ' '.join([self.year_exam_subject, self.get_number_display()])

    def get_absolute_url(self):
        return reverse_lazy('psat:problem-detail', args=[self.id])

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_psat_problem_change', args=[self.id])


class Category(models.Model):
    exam = models.CharField(max_length=2, choices=choices.exam_choice, default='프모', verbose_name='시험')
    unit = models.CharField(max_length=20, choices=choices.unit_choice, default='5급 행정', verbose_name='모집단위')
    department = models.CharField(max_length=40, choices=choices.department_choices, default='5급 일반행정', verbose_name='직렬')
    order = models.SmallIntegerField(default=1, verbose_name='순서')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임] 03_모집단위 및 직렬"
        constraints = [
            models.UniqueConstraint(fields=['exam', 'unit', 'department'], name='unique_prime_category'),
        ]

    def __str__(self):
        return f'[Prime]Category(#{self.id}):{self.unit}-{self.department}'
