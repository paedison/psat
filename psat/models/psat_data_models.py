from ckeditor.fields import RichTextField
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from common.models import User
from reference.models import PsatProblem
from .base_models import Base


class Ratings(models.IntegerChoices):
    STAR1 = 1, '⭐️'
    STAR2 = 2, '⭐️⭐️'
    STAR3 = 3, '⭐️⭐️⭐️'
    STAR4 = 4, '⭐️⭐️⭐️⭐️'
    STAR5 = 5, '⭐️⭐️⭐️⭐️⭐️'


class Answers(models.IntegerChoices):
    ANSWER1 = 1, '①'
    ANSWER2 = 2, '②'
    ANSWER3 = 3, '③'
    ANSWER4 = 4, '④'
    ANSWER5 = 5, '⑤'


class Open(Base):
    user_id = models.IntegerField(blank=True, null=True)
    ip_address = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)


class Like(Base):
    is_liked = models.BooleanField()
    updated_at = models.DateTimeField(auto_now=True)


class Rate(Base):
    rating = models.IntegerField(choices=Ratings.choices)
    updated_at = models.DateTimeField(auto_now=True)


class Solve(Base):
    answer = models.IntegerField(choices=Answers.choices)
    is_correct = models.BooleanField()
    updated_at = models.DateTimeField(auto_now=True)


class Memo(Base):
    memo = RichTextField(config_name='minimal')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user_id", "problem"]]


class Tag(Base):
    tags = TaggableManager()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tagged problem")
        verbose_name_plural = _("Tagged problems")
        unique_together = [["user_id", "problem"]]


class Comment(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='psat_comments')
    problem = models.ForeignKey(PsatProblem, on_delete=models.CASCADE, related_name='comments')
    title = models.TextField(max_length=100)
    comment = RichTextField(config_name='minimal')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='reply_comments')
    hit = models.IntegerField(default=1, verbose_name='조회수')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        year = self.problem.psat.year
        ex = self.problem.psat.exam.abbr[0]
        sub = self.problem.psat.subject.abbr[0]
        num = f'{self.problem.number:02}'
        return f'{year}{ex}{sub}{num}-Comment#{self.id}(User#{self.user_id})'

    def get_absolute_url(self):
        return reverse_lazy('psat:comment_container', args=[self.problem_id])


class Collection(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.IntegerField()
    title = models.CharField(max_length=20)
    order = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['user_id', 'order']
        unique_together = [["user_id", "title"]]

    def __str__(self):
        if self.is_active:
            title = f'[User{self.user_id}_Col{self.id}] {self.title}'
        else:
            title = f'[User{self.user_id}_Col{self.id}_Inactive] {self.title}'
        return title

    def set_active(self):
        self.is_active = True
        self.save()

    def set_inactive(self):
        self.is_active = False
        self.save()


class CollectionItem(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='collection_items')
    problem = models.ForeignKey(PsatProblem, on_delete=models.CASCADE, related_name='collection_items')
    order = models.IntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['collection__user_id', 'collection', 'order']

    def __str__(self):
        return f'{self.collection} - {self.problem}'

    def set_active(self):
        self.is_active = True
        self.save()

    def set_inactive(self):
        self.is_active = False
        self.save()
