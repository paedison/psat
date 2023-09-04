import os
from datetime import datetime

from django.db import models
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.utils.translation import gettext_lazy as _

from taggit.managers import TaggableManager

from _config.settings.base import BASE_DIR
from common.constants import icon
from common.models import User

now = make_aware(datetime.now())

DIFFICULTY_CHOICES = [
    (1, '⭐️'),
    (2, '⭐️⭐️'),
    (3, '⭐️⭐️⭐️'),
    (4, '⭐️⭐️⭐️⭐️'),
    (5, '⭐️⭐️⭐️⭐️⭐️'),
]


class AddInfo:
    is_liked = difficulty_rated = is_correct = None

    def exam_id(self):
        return self.exam.id if isinstance(self, Problem) else self.problem.exam.id

    def year(self):
        return self.exam.year if isinstance(self, Problem) else self.problem.exam.year

    def ex(self):
        return self.exam.ex if isinstance(self, Problem) else self.problem.exam.ex

    def exam1(self):
        return self.exam.exam1 if isinstance(self, Problem) else self.problem.exam.exam1

    def exam2(self):
        return self.exam.exam2 if isinstance(self, Problem) else self.problem.exam.exam2

    def sub(self):
        return self.exam.sub if isinstance(self, Problem) else self.problem.exam.sub

    def subject(self):
        return self.exam.subject if isinstance(self, Problem) else self.problem.exam.subject

    def year_ex_sub(self):
        return self.exam.year_ex_sub if isinstance(self, Problem) else self.problem.exam.year_ex_sub

    def year_ex_sub_hyphen(self):
        year_ex_sub = self.exam.year_ex_sub if isinstance(self, Problem) else self.problem.exam.year_ex_sub
        year, ex, sub = year_ex_sub[:4], year_ex_sub[4:6], year_ex_sub[6:8]
        return f"{year}-{ex}-{sub}"

    def year_ex_sub_hyphen_number(self):
        year_ex_sub = self.exam.year_ex_sub if isinstance(self, Problem) else self.problem.exam.year_ex_sub
        year, ex, sub = year_ex_sub[:4], year_ex_sub[4:6], year_ex_sub[6:8]
        number = self.number if isinstance(self, Problem) else self.problem.number
        return f"{year}-{ex}-{sub} {number}번"

    def full_title(self):
        year = self.exam.year if isinstance(self, Problem) else self.problem.exam.year
        exam2 = self.exam.exam2 if isinstance(self, Problem) else self.problem.exam.exam2
        subject = self.exam.subject if isinstance(self, Problem) else self.problem.exam.subject
        number = self.number if isinstance(self, Problem) else self.problem.number
        return f"{year}년 '{exam2}' {subject} {number}번"

    def prob_id(self):
        return self.id if isinstance(self, Problem) else self.problem.id

    def problem_number(self):
        return self.number if isinstance(self, Problem) else self.problem.number

    def problem_question(self):
        return self.question if isinstance(self, Problem) else self.problem.question

    def correct_answer(self):
        return self.answer if isinstance(self, Problem) else self.problem.answer

    def image_file(self):
        year, year_ex_sub = self.year(), self.year_ex_sub()
        number = f'{self.problem_number():02}'
        static_path = BASE_DIR / 'static'

        preparing_image = static('image/preparing.png')
        file1 = f'PSAT{year_ex_sub}{number}-1.png'
        file2 = f'PSAT{year_ex_sub}{number}-2.png'
        problem_image1 = static(f'image/PSAT/{year}/{file1}')
        problem_image2 = static(f'image/PSAT/{year}/{file2}')

        image1_os_path = os.path.join(static_path, 'image', 'PSAT', str(year), file1)
        image1_exists = os.path.exists(image1_os_path)
        image2_os_path = os.path.join(static_path, 'image', 'PSAT', str(year), file2)
        image2_exists = os.path.exists(image2_os_path)

        image_file = {
            'name1': problem_image1 if image1_exists else preparing_image,
            'tag1': 'Problem Image 1' if image1_exists else 'Preparing Image',
            'name2': problem_image2 if image2_exists else '',
            'tag2': 'Problem Image 2' if image2_exists else '',
        }
        return image_file

    def get_problem_url(self):
        problem_id = self.id if isinstance(self, Problem) else self.problem.id
        return reverse_lazy('psat:problem_detail', kwargs={'problem_id': problem_id})

    def get_like_url(self):
        problem_id = self.id if isinstance(self, Problem) else self.problem.id
        return reverse_lazy('psat:like_detail', kwargs={'problem_id': problem_id})

    def get_rate_url(self):
        problem_id = self.id if isinstance(self, Problem) else self.problem.id
        return reverse_lazy('psat:rate_detail', kwargs={'problem_id': problem_id})

    def get_answer_url(self):
        problem_id = self.id if isinstance(self, Problem) else self.problem.id
        return reverse_lazy('psat:answer_detail', kwargs={'problem_id': problem_id})

    def like_icon(self):
        return icon.PSAT_ICON_SET[f'like{self.is_liked}']

    def rate_icon(self):
        return icon.PSAT_ICON_SET[f'star{self.difficulty_rated}']

    def answer_icon(self):
        return icon.PSAT_ICON_SET[f'answer{self.is_correct}']


class UpdateInfo:
    is_liked = difficulty_rated = is_correct = None
    opened_times = liked_times = rated_times = answered_times = None
    opened_at = liked_at = rated_at = answered_at = None
    submitted_answer = correct_answer = None

    def update_open(self):
        opened_times = self.opened_times or 0
        self.opened_at = now
        self.opened_times = opened_times + 1
        self.save()

    def update_like(self):
        liked_times = self.liked_times or 0
        is_liked = self.is_liked or False
        self.liked_at = now
        self.liked_times = liked_times + 1
        self.is_liked = not is_liked
        self.save()

    def update_rate(self, difficulty):
        rated_times = self.rated_times or 0
        self.rated_at = now
        self.rated_times = rated_times + 1
        self.difficulty_rated = difficulty
        self.save()

    def update_answer(self, answer):
        answered_times = self.answered_times or 0
        self.answered_at = now
        self.answered_times = answered_times + 1
        self.submitted_answer = answer
        if answer == self.correct_answer():
            self.is_correct = True
        else:
            self.is_correct = False
        self.save()


class Exam(AddInfo, models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    year = models.IntegerField()
    ex = models.CharField(max_length=2)
    sub = models.CharField(max_length=2)
    exam1 = models.CharField(max_length=20)
    exam2 = models.CharField(max_length=20)
    subject = models.CharField(max_length=4)
    year_ex_sub = models.CharField(max_length=8)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return self.year_ex_sub_hyphen()

    def get_absolute_url(self):
        return reverse_lazy('psat:problem_list', args=[self.year, self.ex, self.sub])

    def year_ex_sub_hyphen(self):
        return f"{self.year}-{self.ex}-{self.sub}"


class Problem(AddInfo, models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, db_column="exam_id")
    number = models.IntegerField()
    question = models.TextField()
    answer = models.IntegerField()
    tags = TaggableManager()
    # tags = TaggableManager(
    #     verbose_name=_('tags'), blank=True,through=TaggedProblem,
    #     help_text=_('A comma-separated list of tags.'))

    class Meta:
        ordering = ['-exam__year', 'id']

    def __str__(self):
        return self.year_ex_sub_hyphen_number()

    def get_absolute_url(self):
        return reverse_lazy('psat:problem_detail', args=[self.id])


class ProblemData(AddInfo, models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE,
        verbose_name="문제 ID", db_column="problem_id")
    data = models.TextField()

    def __str__(self):
        _year = self.problem.exam.year
        _ex = self.problem.exam.ex
        _sub = self.problem.exam.sub
        _number = self.problem.number
        return f"{_year}-{_ex}-{_sub} {_number}번 자료"


class Evaluation(AddInfo, UpdateInfo, models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="사용자 ID", db_column="user_id")
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        verbose_name="문제 ID", db_column="problem_id")

    opened_at = models.DateTimeField("오픈 일시", null=True)
    opened_times = models.IntegerField("오픈 횟수", null=True)

    liked_at = models.DateTimeField("추천 일시", null=True)
    liked_times = models.IntegerField("추천 횟수", null=True)
    is_liked = models.BooleanField("추천 여부", null=True)

    rated_at = models.DateTimeField("평가 일시", null=True)
    rated_times = models.IntegerField("평가 횟수", null=True)
    difficulty_rated = models.IntegerField(
        "평가 난이도", null=True, choices=DIFFICULTY_CHOICES)

    answered_at = models.DateTimeField("정답확인 일시", null=True)
    answered_times = models.IntegerField("정답확인 횟수", null=True)
    submitted_answer = models.IntegerField("제출 정답", null=True)
    is_correct = models.BooleanField("정오 여부", null=True)

    class Meta:
        ordering = ['-problem__exam__year', 'problem__exam__id', 'problem__number']


class ProblemMemo(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="사용자 ID", db_column="user_id")
    problem = models.ForeignKey(
        Problem, on_delete=models.CASCADE,
        verbose_name="문제 ID", db_column="problem_id")
    content = models.TextField("내용")
    created_at = models.DateTimeField("작성일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        unique_together = [["user", "problem"]]


class ProblemTag(models.Model):
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="사용자 ID", db_column="user_id")
    problem = models.ForeignKey(
        'Problem', on_delete=models.CASCADE,
        verbose_name="문제 ID", db_column="problem_id")
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tagged problem")
        verbose_name_plural = _("Tagged problems")
        unique_together = [["user", "problem"]]
