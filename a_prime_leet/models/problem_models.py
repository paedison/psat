from datetime import datetime, timedelta

from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone

from . import choices, querysets


class Leet(models.Model):
    year = models.PositiveSmallIntegerField(choices=choices.year_choice, default=datetime.now().year + 1, verbose_name='연도')
    exam = models.CharField(max_length=2, choices=choices.exam_choice, default='프모', verbose_name='시험')
    round = models.PositiveSmallIntegerField(default=1, verbose_name='회차')
    name = models.CharField(max_length=30, verbose_name='시험명')
    abbr = models.CharField(max_length=30, verbose_name='약칭')
    is_active = models.BooleanField(default=False, verbose_name='활성')

    page_opened_at = models.DateTimeField(default=timezone.now, verbose_name='페이지 오픈 일시')
    exam_started_at = models.DateTimeField(default=timezone.now, verbose_name='시험 시작 일시')
    exam_finished_at = models.DateTimeField(default=timezone.now, verbose_name='시험 종료 일시')
    answer_predict_opened_at = models.DateTimeField(default=timezone.now, verbose_name='예상 정답 공개 일시')
    answer_official_opened_at = models.DateTimeField(default=timezone.now, verbose_name='공식 정답 공개 일시')
    predict_closed_at = models.DateTimeField(default=timezone.now, verbose_name='성적 에측 종료 일시')

    class Meta:
        verbose_name = verbose_name_plural = "[프라임LEET] 00_LEET 모의고사"
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(fields=['year', 'exam', 'name'], name='unique_prime_leet_leet'),
        ]

    def __str__(self):
        return self.name

    @property
    def score_opened_at(self):
        score_open_date = self.answer_official_opened_at + timedelta(days=5)
        return score_open_date.replace(hour=8, minute=0)

    @property
    def reference(self):
        return self.name

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
        return self.predict_closed_at <= timezone.now()

    @staticmethod
    def get_admin_list_url():
        return reverse_lazy('prime_leet:admin-list')

    def get_admin_leet_active_url(self):
        return reverse_lazy('prime_leet:admin-leet-active', args=[self.id])

    def get_admin_detail_url(self, model_type: str):
        return reverse_lazy('prime_leet:admin-detail', args=[model_type, self.id])

    def get_admin_predict_detail_url(self):
        return reverse_lazy('prime_leet:admin-detail', args=['predict', self.id])

    def get_admin_result_detail_url(self):
        return reverse_lazy('prime_leet:admin-detail', args=['result', self.id])

    def get_admin_fake_detail_url(self):
        return reverse_lazy('prime_leet:admin-detail', args=['fake', self.id])

    def get_admin_update_url(self):
        return reverse_lazy('prime_leet:admin-update', args=[self.id])

    @staticmethod
    def get_result_list_url():
        return reverse_lazy('prime_leet:result-list')

    def get_result_detail_url(self):
        return reverse_lazy('prime_leet:result-detail', args=[self.id])

    def get_result_print_url(self):
        return reverse_lazy('prime_leet:result-print', args=[self.id])

    @staticmethod
    def get_predict_list_url():
        return reverse_lazy('prime_leet:predict-list')

    def get_predict_detail_url(self):
        return reverse_lazy('prime_leet:predict-detail', args=[self.id])

    @staticmethod
    def get_predict_student_register_url():
        return reverse_lazy('prime_leet:predict-student-register')

    def get_predict_answer_input_url(self, subject_field):
        return reverse_lazy('prime_leet:predict-answer-input', args=[self.id, subject_field])

    def get_predict_answer_confirm_url(self, subject_field):
        return reverse_lazy('prime_leet:predict-answer-confirm', args=[self.id, subject_field])


class Problem(models.Model):
    objects = querysets.ProblemQuerySet.as_manager()
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
        return self.reference

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
