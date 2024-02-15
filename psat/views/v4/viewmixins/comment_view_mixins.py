from bs4 import BeautifulSoup as bs
from django.core.paginator import Paginator
from django.db.models import F

from common.constants.icon_set import ConstantIconSet
from psat import forms as custom_forms
from psat import models as custom_models
from reference.models import psat_models as reference_models


class BaseMixIn(ConstantIconSet):
    """Setting mixin for Memo views."""
    request: any
    kwargs: dict
    object: any

    model = custom_models.Comment
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'
    form_class = custom_forms.CommentForm
    context_object_name = 'comments'
    template_name = 'psat/v4/snippets/comment_container.html'

    problem_id: int
    comment_id: str
    parent_id: str
    problem: reference_models.PsatProblem.objects
    comment: reference_models.PsatProblem.objects
    parent_comment: reference_models.PsatProblem.objects

    page_number: str

    def get_properties(self):
        self.comment_id = self.kwargs.get('comment_id')
        self.problem_id = self.kwargs.get('problem_id')
        self.parent_id = self.request.GET.get('parent_id')
        self.comment = custom_models.Comment.objects.none()
        self.problem = reference_models.PsatProblem.objects.none()
        self.parent_comment = custom_models.Comment.objects.none()

        if self.problem_id:
            self.problem = reference_models.PsatProblem.objects.get(id=self.problem_id)
        elif self.comment_id:
            self.comment = (
                custom_models.Comment.objects.select_related('user')
                .annotate(username=F('user__username')).get(id=self.comment_id)
            )
        if self.parent_id:
            self.parent_comment = (
                custom_models.Comment.objects.select_related('user')
                .annotate(username=F('user__username')).get(id=self.parent_id)
            )


class CommentListViewMixin(BaseMixIn):
    paginate_by = 10

    page_obj: any
    page_range: any
    num_pages: any

    def get_properties(self):
        super().get_properties()

        self.page_number = self.request.GET.get('page', '1')
        self.page_obj, self.page_range, self.num_pages = self.get_paginator_info()

    def get_paginator_info(self) -> tuple[object, object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        queryset = self.get_queryset()

        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(number=self.page_number, on_each_side=3, on_ends=1)
        num_pages = paginator.num_pages
        return page_obj, page_range, num_pages

    def get_queryset(self):
        qs = (
            self.model.objects
            .select_related(
                'user', 'problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
            .annotate(
                username=F('user__username'),
                year=F('problem__psat__year'), number=F('problem__number'),
                ex=F('problem__psat__exam__abbr'), exam=F('problem__psat__exam__name'),
                sub=F('problem__psat__subject__abbr'), subject=F('problem__psat__subject__name'))
        )
        parent_comments = qs.filter(parent__isnull=True).order_by('-timestamp')
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')

        all_comments = []
        for comment in parent_comments:
            all_comments.append(comment)
            all_comments.extend(child_comments.filter(parent=comment))

        return all_comments


class CommentContainerViewMixin(CommentListViewMixin):
    paginate_by = 5

    def get_queryset(self):
        qs = (
            self.model.objects.filter(problem_id=self.problem_id)
            .select_related('user').annotate(username=F('user__username'))
        )
        parent_comments = qs.filter(parent__isnull=True).order_by('-timestamp')
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')

        all_comments = []
        for comment in parent_comments:
            all_comments.append(comment)
            all_comments.extend(child_comments.filter(parent=comment))

        return all_comments


class CommentCreateViewMixin(BaseMixIn):
    comment_title: str

    def get_properties(self):
        super().get_properties()

        if self.request.method == 'GET':
            self.page_number = self.request.GET.get('page', '1')
        else:
            self.page_number = self.request.POST.get('page', '1')
        print(self.page_number)

        self.comment_title = self.get_comment_title()

    def get_comment_title(self):
        comment = self.request.POST.get('comment')
        if comment:
            soup = bs(comment, 'html.parser')
            text_comment = soup.get_text()
            comment_title = text_comment[:20]
            return comment_title
