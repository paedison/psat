from datetime import datetime

from ckeditor.fields import RichTextField
from django.db import models
from django.templatetags.static import static
from django.urls import reverse_lazy
from taggit.managers import TaggableManager, _TaggableManager  # noqa
from taggit.models import TaggedItemBase, TagBase

from _config.settings.base import BASE_DIR
from a_psat.models import choices
from a_psat.models.queryset import official_queryset as queryset
from common.constants import icon_set_new
from common.models import User


class Psat(models.Model):
    objects = queryset.PsatQuerySet.as_manager()
    year = models.IntegerField(choices=choices.year_choice, default=datetime.now().year, verbose_name='연도')
    exam = models.CharField(max_length=2, choices=choices.exam_choice, default='행시', verbose_name='시험')
    order = models.IntegerField(verbose_name='순서')
    is_active = models.BooleanField(default=False, verbose_name='활성')

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 00_PSAT"
        ordering = ['-year', 'order']
        constraints = [
            models.UniqueConstraint(fields=['year', 'exam'], name='unique_psat'),
        ]

    def __str__(self):
        return f'[PSAT]Psat(#{self.id}):{self.year}-{self.order}-{self.exam}'

    @property
    def reference(self):
        return f'{self.year}{self.exam}'

    @property
    def full_reference(self):
        return ' '.join([self.get_year_display(), self.exam_name])

    @property
    def exam_name(self):
        if self.exam == '행시':
            return '행정고시' if self.year < 2011 else '5급공채'
        if self.exam == '외시':
            return '외교원' if self.year == 2013 else '외무고시'
        if self.exam == '칠급':
            return '7급공채 모의고사' if self.year == 2020 else '7급공채'
        return self.get_exam_display()

    @property
    def exam_abbr(self):
        exam_dict = {
            '행시': '5급공채 등',
            '입시': '입법고시',
            '칠급': '7급공채 등',
        }
        return exam_dict[self.exam]

    def get_admin_psat_active_url(self):
        return reverse_lazy('psat:admin-official-psat-active', args=[self.id])

    def get_admin_official_detail_url(self):
        return reverse_lazy('psat:admin-official-detail', args=[self.id])

    def get_admin_official_update_by_psat_url(self):
        return reverse_lazy('psat:admin-official-update-by-psat', args=[self.id])

    def get_admin_predict_detail_url(self):
        return reverse_lazy('psat:admin-predict-detail', args=[self.id])

    def get_admin_study_detail_url(self):
        return reverse_lazy('psat:admin-study-detail', args=[self.id])

    def get_admin_predict_update_url(self):
        return reverse_lazy('psat:admin-predict-update', args=[self.id])

    def get_admin_predict_statistics_print_url(self):
        return reverse_lazy('psat:admin-predict-statistics-print', args=[self.id])

    def get_admin_predict_catalog_print_url(self):
        return reverse_lazy('psat:admin-predict-catalog-print', args=[self.id])

    def get_admin_predict_answer_print_url(self):
        return reverse_lazy('psat:admin-predict-answer-print', args=[self.id])

    def get_admin_predict_statistics_excel_url(self):
        return reverse_lazy('psat:admin-predict-statistics-excel', args=[self.id])

    def get_admin_predict_prime_id_excel_url(self):
        return reverse_lazy('psat:admin-predict-prime_id-excel', args=[self.id])

    def get_admin_predict_catalog_excel_url(self):
        return reverse_lazy('psat:admin-predict-catalog-excel', args=[self.id])

    def get_admin_predict_answer_excel_url(self):
        return reverse_lazy('psat:admin-predict-answer-excel', args=[self.id])

    @staticmethod
    def get_predict_list_url():
        return reverse_lazy('psat:predict-list')

    def get_predict_detail_url(self):
        return reverse_lazy('psat:predict-detail', args=[self.id])

    @staticmethod
    def get_predict_register_url():
        return reverse_lazy('psat:predict-register')

    def get_predict_answer_input_url(self, subject_field):
        return reverse_lazy('psat:predict-answer-input', args=[self.id, subject_field])

    def get_predict_answer_confirm_url(self, subject_field):
        return reverse_lazy('psat:predict-answer-confirm', args=[self.id, subject_field])

    def get_predict_modal_url(self):
        return reverse_lazy('psat:predict-modal', args=[self.id])


class ProblemTag(TagBase):
    objects = queryset.ProblemTagQuerySet.as_manager()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 07_태그"
        db_table = 'a_psat_problem_tag'


class ProblemTaggedItem(TaggedItemBase):
    tag = models.ForeignKey(ProblemTag, on_delete=models.CASCADE, related_name="tagged_items")
    content_object = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='tagged_problems')
    user = models.ForeignKey(User, related_name='psat_tagged_items', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 08_태그된 문제"
        ordering = ['-id']
        db_table = 'a_psat_problem_tagged_item'

    @property
    def tag_name(self):
        return self.tag.name

    @property
    def reference(self):
        return self.content_object.reference


class _ProblemTagManager(_TaggableManager):
    def names(self):
        return self.get_queryset({'tagged_items__is_active': True}).values_list("name", flat=True).distinct()


class Problem(models.Model):
    objects = queryset.ProblemQuerySet.as_manager()
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='problems', verbose_name='PSAT')
    subject = models.CharField(max_length=2, choices=choices.subject_choice, default='언어', verbose_name='과목')
    paper_type = models.CharField(max_length=2, default='', verbose_name='책형')
    number = models.IntegerField(choices=choices.number_choice, default=1, verbose_name='번호')
    answer = models.IntegerField(choices=choices.answer_choice, default=1, verbose_name='정답')
    question = models.TextField(default='', verbose_name='발문')
    data = models.TextField(default='', verbose_name='자료')

    tags = TaggableManager(through=ProblemTaggedItem, blank=True, manager=_ProblemTagManager)

    like_users = models.ManyToManyField(User, related_name='liked_psat_problems', through='ProblemLike')
    rate_users = models.ManyToManyField(User, related_name='rated_psat_problems', through='ProblemRate')
    solve_users = models.ManyToManyField(User, related_name='solved_psat_problems', through='ProblemSolve')
    memo_users = models.ManyToManyField(User, related_name='memoed_psat_problems', through='ProblemMemo')
    comment_users = models.ManyToManyField(User, related_name='commented_psat_problems', through='ProblemComment')
    collections = models.ManyToManyField(
        'ProblemCollection', related_name='collected_psat_problems', through='ProblemCollectionItem')

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 01_문제"
        ordering = ['psat', 'id']
        constraints = [
            models.UniqueConstraint(fields=['psat', 'subject', 'number'], name='unique_problem'),
        ]

    def __str__(self):
        return f'[PSAT]Problem(#{self.id}):{self.reference}'

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
    def reference2(self):
        return f'{self._reference}{self.paper_type[0]}-{self.number:02}'

    @property
    def year_exam_subject(self):
        return ' '.join([self.psat.get_year_display(), self.psat.exam_name, self.get_subject_display()])

    @property
    def full_reference(self):
        return ' '.join([self.year_exam_subject, self.get_number_display()])

    @property
    def img_name(self):
        return f'PSAT{self.year_ex_sub}{self.number:02}'

    @property
    def static_img_path(self):
        return f'image/PSAT/{self.psat.year}/{self.img_name}.png'

    @property
    def relative_img_path(self):
        return static(self.static_img_path)

    @property
    def absolute_img_path(self):
        return BASE_DIR / 'static' / self.static_img_path

    @property
    def has_image(self) -> bool:
        return self.absolute_img_path.exists()

    @property
    def bg_color(self):
        bg_color_dict = {
            '헌법': 'bg_heonbeob',
            '언어': 'bg_eoneo',
            '자료': 'bg_jaryo',
            '상황': 'bg_sanghwang',
        }
        return bg_color_dict[self.subject]

    @property
    def icon(self):
        return {
            'nav': icon_set_new.ICON_NAV,
            'like': icon_set_new.ICON_LIKE,
            'rate': icon_set_new.ICON_RATE,
            'solve': icon_set_new.ICON_SOLVE,
            'memo': icon_set_new.ICON_MEMO,
            'tag': icon_set_new.ICON_TAG,
            'collection': icon_set_new.ICON_COLLECTION,
            'question': icon_set_new.ICON_QUESTION,
        }

    def get_absolute_url(self):
        return reverse_lazy('psat:problem-detail', args=[self.id])

    def get_like_url(self):
        return reverse_lazy('psat:like-problem', args=[self.id])

    def get_rate_url(self):
        return reverse_lazy('psat:rate-problem', args=[self.id])

    def get_solve_url(self):
        return reverse_lazy('psat:solve-problem', args=[self.id])

    def get_tag_url(self):
        return reverse_lazy('psat:tag-problem', args=[self.id])

    def get_collect_url(self):
        return reverse_lazy('psat:collect-problem', args=[self.id])

    def get_annotate_url(self):
        return reverse_lazy('psat:annotate-problem', args=[self.id])

    def get_comment_create_url(self):
        return reverse_lazy('psat:comment-problem-create', args=[self.id])

    def get_admin_change_url(self):
        return reverse_lazy('admin:a_psat_problem_change', args=[self.id])


class ProblemOpen(models.Model):
    objects = queryset.ProblemOpenQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user_id = models.IntegerField(blank=True, null=True)
    ip_address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 02_확인기록"
        ordering = ['-id']
        db_table = 'a_psat_problem_open'

    def __str__(self):
        return f'[PSAT]ProblemOpen(#{self.id}):{self.problem.reference}-{self.user_id}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemLike(models.Model):
    objects = queryset.ProblemLikeQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_liked = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 03_즐겨찾기"
        ordering = ['-id']
        db_table = 'a_psat_problem_like'

    def __str__(self):
        if self.is_liked:
            return f'[PSAT]ProblemLike(#{self.id}):{self.problem.reference}(Liked)-{self.user.username}'
        return f'[PSAT]ProblemLike(#{self.id}):{self.problem.reference}(Unliked)-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemRate(models.Model):
    class Ratings(models.IntegerChoices):
        STAR1 = 1, '⭐️'
        STAR2 = 2, '⭐️⭐️'
        STAR3 = 3, '⭐️⭐️⭐️'
        STAR4 = 4, '⭐️⭐️⭐️⭐️'
        STAR5 = 5, '⭐️⭐️⭐️⭐️⭐️'

    objects = queryset.ProblemRateQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='rates')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_rates')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    rating = models.IntegerField(choices=Ratings.choices)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 04_난이도"
        ordering = ['-id']
        db_table = 'a_psat_problem_rate'

    def __str__(self):
        return f'[PSAT]ProblemRate(#{self.id}):{self.problem.reference}({self.rating})-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemSolve(models.Model):
    class Answers(models.IntegerChoices):
        ANSWER1 = 1, '①'
        ANSWER2 = 2, '②'
        ANSWER3 = 3, '③'
        ANSWER4 = 4, '④'
        ANSWER5 = 5, '⑤'

    objects = queryset.ProblemSolveQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='solves')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_solves')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    answer = models.IntegerField(choices=Answers.choices)
    is_correct = models.BooleanField()

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 05_정답확인"
        ordering = ['-id']
        db_table = 'a_psat_problem_solve'

    def __str__(self):
        if self.is_correct:
            return f'[PSAT]ProblemSolve(#{self.id}):{self.problem.reference}(Correct)-{self.user.username}'
        return f'[PSAT]ProblemSolve(#{self.id}):{self.problem.reference}(Wrong)-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemMemo(models.Model):
    objects = queryset.ProblemMemoQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='memos')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_memos')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    content = RichTextField(config_name='minimal')

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 06_메모"
        ordering = ['-id']
        db_table = 'a_psat_problem_memo'

    def __str__(self):
        return f'[PSAT]ProblemMemo(#{self.id}):{self.problem.reference}-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference

    def get_memo_url(self):
        return reverse_lazy('psat:memo-problem', args=[self.problem_id])


class ProblemCollection(models.Model):
    objects = queryset.ProblemCollectionQuerySet.as_manager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_collections')
    title = models.CharField(max_length=20)
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 09_컬렉션"
        ordering = ['-id']
        db_table = 'a_psat_problem_collection'

    def __str__(self):
        return f'[PSAT]ProblemCollection(#{self.id}):{self.title}-{self.user.username}'


class ProblemCollectionItem(models.Model):
    objects = queryset.ProblemCollectionItemQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='collected_problems')
    collection = models.ForeignKey(ProblemCollection, on_delete=models.CASCADE, related_name='collection_items')
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = verbose_name_plural = "[기출문제] 10_컬렉션 문제"
        ordering = ['-id']
        db_table = 'a_psat_problem_collection_item'

    def __str__(self):
        return f'[PSAT]ProblemCollectionItem(#{self.id}):{self.collection.title}-{self.problem.reference}'

    @property
    def collect_title(self):
        return self.collection.title

    @property
    def reference(self):
        return self.problem.reference


class ProblemAnnotation(models.Model):
    objects = queryset.ProblemAnnotationQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_annotations')
    annotate_type = models.CharField(max_length=50)
    image = models.ImageField(upload_to='annotations/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']
        db_table = 'a_psat_problem_annotation'


class ProblemComment(models.Model):
    objects = queryset.ProblemCommentQuerySet.as_manager()
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_comments')
    content = models.TextField()
    like_users = models.ManyToManyField(
        User, related_name='liked_psat_problem_comments', through='ProblemCommentLike')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='reply_comments')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        db_table = 'a_psat_problem_comment'

    def __str__(self):
        prefix = '↪ ' if self.parent else ''
        return f'{prefix}[PSAT]ProblemComment(#{self.id}):{self.problem.reference}-{self.user.username}'

    @property
    def reference(self):
        return self.problem.reference


class ProblemCommentLike(models.Model):
    objects = queryset.ProblemCommentLikeQuerySet.as_manager()
    comment = models.ForeignKey(ProblemComment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_problem_comment_likes')
    is_liked = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'a_psat_problem_comment_like'

    def __str__(self):
        return f'[PSAT]ProblemCommentLike(#{self.id}):{self.comment.problem.reference}-{self.user.username}'

    @property
    def reference(self):
        return self.comment.problem.reference
