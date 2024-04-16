from bs4 import BeautifulSoup as bs
from django.core.paginator import Paginator
from django.db.models import F
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from psat import forms as custom_forms
from psat import models as custom_models
from reference.models import psat_models as reference_models


class BaseMixIn(ConstantIconSet):
    """Setting mixin for Collection views."""
    request: any
    kwargs: dict
    object: any

    model = custom_models.Collection
    lookup_field = 'id'
    lookup_url_kwarg = 'collection_id'
    form_class = custom_forms.CollectionForm
    context_object_name = 'collections'
    template_name = 'psat/v4/snippets/collection.html'

    collection_model = custom_models.Collection
    item_model = custom_models.CollectionItem

    user_id: int | None
    problem_id: int
    collection_id: str

    problem: reference_models.PsatProblem.objects
    collection: custom_models.Collection.objects
    collection_items: custom_models.CollectionItem.objects

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None
        self.collection_id = self.kwargs.get('collection_id')
        self.problem_id = self.kwargs.get('problem_id')

        self.problem = reference_models.PsatProblem.objects.none()
        self.collection = self.collection_model.objects.none()
        self.collection_items = self.item_model.objects.none()

        if self.problem_id:
            self.problem = reference_models.PsatProblem.objects.get(id=self.problem_id)
        if self.collection_id:
            self.collection = self.collection_model.objects.get(id=self.collection_id)
            self.collection_items = self.get_collection_items_qs()

    def get_collection_qs(self):
        return (
            self.collection_model.objects
            .filter(user_id=self.user_id, is_active=True)
        )

    def get_collection_items_qs(self, collection_id=None):
        collection_id = collection_id or self.collection_id
        return (
            self.item_model.objects
            .filter(collection_id=collection_id, is_active=True)
            .select_related('problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
            .annotate(
                year=F('problem__psat__year'),
                ex=F('problem__psat__exam__abbr'),
                sub=F('problem__psat__subject__abbr'),
                number=F('problem__number'),
                question=F('problem__question'),
            )
        )

    def get_collection_item_qs(self, item_id):
        return (
            self.item_model.objects
            .select_related('problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
            .annotate(
                year=F('problem__psat__year'),
                ex=F('problem__psat__exam__abbr'),
                sub=F('problem__psat__subject__abbr'),
                number=F('problem__number'),
                question=F('problem__question'),
            ).get(id=item_id)
        )

    @staticmethod
    def get_url(name, *args):
        if args:
            base_url = reverse_lazy(f'psat:{name}', args=[*args])
            return f'{base_url}?'
        base_url = reverse_lazy(f'psat:{name}')
        return f'{base_url}?'

    def get_paginator_info(self, page_data, per_page=10) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(page_data, per_page)
        try:
            page_obj = paginator.get_page(page_number)
            page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
            return page_obj, page_range
        except TypeError:
            return None, None


class CommentContainerViewMixin(BaseMixIn):
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


class CollectionCreateViewMixin(BaseMixIn):
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
