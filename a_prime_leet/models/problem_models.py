from datetime import datetime
from django.utils import timezone

from django.db import models
from django.urls import reverse_lazy

from . import choices


class Leet(models.Model):
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
        verbose_name = verbose_name_plural = "[프라임LEET] 00_LEET 모의고사"
        ordering = ['-year', 'round']
        constraints = [
            models.UniqueConstraint(fields=['year', 'exam', 'round'], name='unique_prime_leet_leet'),
        ]

    def __str__(self):
        return f'[PrimeLeet]Leet(#{self.id}):{self.reference}'

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
        return reverse_lazy('prime_leet:score-admin-list')

    def get_admin_detail_url(self):
        return reverse_lazy('prime_leet:score-admin-detail', args=[self.id])

    def get_admin_update_url(self):
        return reverse_lazy('prime_leet:score-admin-update', args=[self.id])

    @staticmethod
    def get_score_list_url():
        return reverse_lazy('prime_leet:score-list')

    def get_score_detail_url(self):
        return reverse_lazy('prime_leet:score-detail', args=[self.id])

    def get_score_register_url(self):
        return reverse_lazy('prime_leet:score-register', args=[self.id])

    def get_score_unregister_url(self):
        return reverse_lazy('prime_leet:score-unregister', args=[self.id])

    def get_score_print_url(self):
        return reverse_lazy('prime_leet:score-print', args=[self.id])

    def get_score_modal_url(self):
        return reverse_lazy('prime_leet:score-modal', args=[self.id])


class Problem(models.Model):
    leet = models.ForeignKey(Leet, on_delete=models.CASCADE, related_name='problems', verbose_name='Leet')
    subject = models.CharField(max_length=2, choices=choices.subject_choice, default='언어', verbose_name='과목')
    number = models.IntegerField(choices=choices.number_choice, default=1, verbose_name='번호')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='정답')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임LEET] 01_문제"
        ordering = ['leet', 'id']
        constraints = [
            models.UniqueConstraint(fields=['leet', 'subject', 'number'], name='unique_prime_leet_problem'),
        ]

    def __str__(self):
        return f'[PrimeLeet]Problem(#{self.id}):{self.reference}'

    @property
    def year_ex_sub(self):
        return f'{self.leet.year}{self.leet.exam}{self.subject}'

    @property
    def _reference(self):
        return f'{self.leet.year}{self.leet.exam[0]}{self.subject[0]}'

    @property
    def reference(self):
        return f'{self._reference}-{self.number:02}'

    @property
    def year_exam_subject(self):
        return ' '.join([self.leet.get_year_display(), self.leet.get_exam_display(), self.get_subject_display()])

    @property
    def full_reference(self):
        return ' '.join([self.year_exam_subject, self.get_number_display()])