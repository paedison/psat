from bs4 import BeautifulSoup as bs
from django.db.models import F

from common.constants.icon_set import ConstantIconSet
from psat import forms, models, utils
from reference.models import psat_models


class BaseMixIn(ConstantIconSet):
    """Setting mixin for Comment views."""
    request: any
    kwargs: dict
    object: any

    model = models.Comment
    form_class = forms.CommentForm

    comment_model = models.Comment
    problem_model = psat_models.PsatProblem

    @staticmethod
    def get_url(name, *args):
        return utils.get_url(name, *args)

    def get_comment_qs(self):
        return (
            self.comment_model.objects
            .select_related(
                'user', 'problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
            .annotate(
                username=F('user__username'),
                year=F('problem__psat__year'), number=F('problem__number'),
                ex=F('problem__psat__exam__abbr'), exam=F('problem__psat__exam__name'),
                sub=F('problem__psat__subject__abbr'), subject=F('problem__psat__subject__name')))

    def get_single_comment(self, comment_id):
        if comment_id:
            return self.get_comment_qs().get(id=comment_id)

    def get_all_comments(self, problem_id=None):
        qs = self.get_comment_qs()
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        parent_comments = qs.filter(parent__isnull=True).order_by('-timestamp')
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
        all_comments = []
        for comment in parent_comments:
            all_comments.append(comment)
            all_comments.extend(child_comments.filter(parent=comment))
        return all_comments

    def get_all_comments_of_parent_comment(self, parent_comment):
        qs = self.get_comment_qs().filter(parent=parent_comment)
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
        all_comments = [parent_comment]
        for comment in child_comments:
            all_comments.append(comment)
        return all_comments

    def get_comment_title(self):
        comment = self.request.POST.get('comment')
        if comment:
            soup = bs(comment, 'html.parser')
            text_comment = soup.get_text()
            comment_title = text_comment[:20]
            return comment_title

    def get_additional_data_for_create(self, form):
        problem_id = self.kwargs.get('problem_id')
        form.user = self.request.user
        form.problem_id = problem_id
        form.title = self.get_comment_title()
        return form

    @staticmethod
    def get_sub_title_from_comment(comment):
        return f'{comment.year}년 {comment.exam} {comment.subject} {comment.number}번'

    def get_replies_from_comment(self, comment):
        return self.comment_model.objects.filter(parent=comment)

    def get_problem(self, problem_id):
        return self.problem_model.objects.get(id=problem_id)

    def get_problem_from_problem_id(self, problem_id):
        return (
            self.problem_model.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .get(id=problem_id)
        )


    def get_paginator_info(self, page_data, per_page=10) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        return utils.get_page_obj_and_range(page_number, page_data, per_page)
