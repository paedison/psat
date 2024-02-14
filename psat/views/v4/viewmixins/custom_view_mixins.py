from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from taggit import models as taggit_models
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import get_weight_fun

from common.constants.icon_set import ConstantIconSet
from dashboard.models import psat_data_models
from psat import forms as custom_forms
from psat import models as custom_models
from reference.models import psat_models as reference_models


class CustomUpdateViewMixIn(ConstantIconSet):
    """Represent PSAT custom data update view mixin."""
    request: any
    kwargs: dict

    user_id: int | None
    view_type: str

    problem_id: int
    problem: reference_models.PsatProblem.objects

    is_liked: str | bool
    rating: str | int
    answer: int

    ip_address: str

    option_name: str
    find_filter: dict
    data_instance: custom_models.Like | custom_models.Rate | custom_models.Solve

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None
        self.view_type = self.kwargs.get('view_type', 'problem')

        self.problem_id = int(self.kwargs.get('problem_id'))
        self.problem = self.get_problem()

        is_liked = self.request.POST.get('is_liked', '')
        is_liked_dict = {'True': True, 'False': False, 'None': False}
        self.is_liked = '' if is_liked == '' else not is_liked_dict[is_liked]

        self.rating = self.request.POST.get('rating', '')
        self.answer = self.request.POST.get('answer', '')

        rating = self.request.POST.get('rating', '')
        self.rating = '' if rating == '' else int(rating)

        answer = self.request.POST.get('answer', '')
        self.answer = '' if answer == '' else int(answer)

        self.ip_address = self.request.META.get('REMOTE_ADDR')

    def get_problem(self):
        return (
            reference_models.PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .get(id=self.problem_id)
        )

    def get_option_name(self) -> str:
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        return option_dict[self.view_type]

    def get_find_filter(self) -> dict:
        find_filter = {
            'problem_id': self.problem_id,
            'user_id': self.user_id,
        }
        if not self.user_id:
            find_filter['ip_address'] = self.ip_address
        return find_filter

    def get_update_filter(self) -> dict:
        filter_expr = {
            'problem': {},
            'like': {'is_liked': self.is_liked},
            'rate': {'rating': self.rating},
            'solve': {
                'answer': self.answer,
                'is_correct': self.answer == self.problem.answer,
            },
        }
        return filter_expr[self.view_type]

    def get_create_filter(self, find_filter) -> dict:
        create_filter = find_filter.copy()
        update_expr = {
            'problem': {},
            'like': {'is_liked': self.is_liked},
            'rate': {'rating': self.rating},
            'solve': {
                'answer': self.answer,
                'is_correct': self.answer == self.problem.answer,
            },
        }
        create_filter.update(update_expr[self.view_type])
        return create_filter

    def get_data_instance(self, find_filter):
        model_dict = {
            'like': custom_models.Like,
            'rate': custom_models.Rate,
            'solve': custom_models.Solve,
        }
        data_model = model_dict[self.view_type]

        if data_model:
            try:
                instance = data_model.objects.get(**find_filter)
                update_filter = self.get_update_filter()
                for key, item in update_filter.items():
                    setattr(instance, key, item)
                instance.save()
            except ObjectDoesNotExist:
                create_filter = self.get_create_filter(find_filter)
                instance = data_model.objects.create(**create_filter)
            return instance

    def make_log_instance(self, data_instance, find_filter):
        create_filter = self.get_create_filter(find_filter)
        if data_instance:
            model_dict = {
                'like': psat_data_models.PsatLikeLog,
                'rate': psat_data_models.PsatRateLog,
                'solve': psat_data_models.PsatSolveLog,
            }
            model = model_dict[self.view_type]
            data_id = data_instance.id
            recent_log = model.objects.filter(**find_filter).order_by('-id').first()
            repetition = recent_log.repetition + 1 if recent_log else 1
            create_filter.update(
                {'repetition': repetition, 'data_id': data_id}
            )
            model.objects.create(**create_filter)


class SolveModalViewMixIn(ConstantIconSet):
    """Represent PSAT Solve data update modal view mixin."""
    request: any
    problem_id: int
    answer: int
    is_correct: bool | None

    def get_properties(self):
        self.problem_id = int(self.request.POST.get('problem_id'))

        answer = self.request.POST.get('answer')
        self.answer = int(answer) if answer else None

        problem = reference_models.PsatProblem.objects.get(id=self.problem_id)
        self.is_correct = None if self.answer is None else (self.answer == problem.answer)


class MemoViewMixIn(ConstantIconSet):
    """Setting mixin for Memo views."""
    model = custom_models.Memo
    lookup_field = 'id'
    lookup_url_kwarg = 'memo_id'
    form_class = custom_forms.MemoForm
    context_object_name = 'my_memo'
    template_name = 'psat/v4/snippets/memo_container.html'

    request: any
    kwargs: dict
    object: any
    user_id: int | None

    memo_id: str
    problem_id: str

    my_memo: custom_models.Memo.objects
    problem: reference_models.PsatProblem.objects

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None

        self.memo_id = self.kwargs.get('memo_id')
        self.problem_id = self.kwargs.get('problem_id')
        self.my_memo = custom_models.Memo.objects.none()
        self.problem = reference_models.PsatProblem.objects.none()

        if self.memo_id:
            self.my_memo = custom_models.Memo.objects.get(id=self.memo_id)
            self.problem = reference_models.PsatProblem.objects.get(id=self.my_memo.problem_id)
        elif self.problem_id:
            self.problem = reference_models.PsatProblem.objects.get(id=self.problem_id)
            self.my_memo = custom_models.Memo.objects.filter(
                problem=self.problem, user_id=self.user_id).first()


class TagViewMixIn(ConstantIconSet):
    """Setting mixin for Tag views."""
    menu = 'tag'
    model = custom_models.Tag
    lookup_field = 'id'
    lookup_url_kwarg = 'tag_id'
    form_class = custom_forms.TagForm
    context_object_name = 'my_tag'
    template_name = 'psat/v4/snippets/tag_container.html'

    object: any
    request: any
    kwargs: dict
    user_id: int | None

    tag_id: str
    problem_id: str

    my_tag: custom_models.Tag.objects
    problem: reference_models.PsatProblem.objects
    content_type: str

    info: dict

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None

        self.tag_id = self.kwargs.get('tag_id')
        self.problem_id = self.kwargs.get('problem_id')
        self.my_tag = custom_models.Tag.objects.none()
        self.problem = reference_models.PsatProblem.objects.none()

        if self.tag_id:
            self.my_tag = custom_models.Tag.objects.get(id=self.tag_id)
            self.problem = reference_models.PsatProblem.objects.get(id=self.my_tag.problem_id)
        elif self.problem_id:
            self.problem = reference_models.PsatProblem.objects.get(id=self.problem_id)
            self.my_tag = custom_models.Tag.objects.filter(
                problem=self.problem, user_id=self.user_id).first()

        self.content_type: str = ContentType.objects.get(app_label='psat', model='tag')

        self.info = {
            'menu': 'psat',
            'view_type': 'tag',
        }

    def get_my_tag_list(self) -> list | None:
        """Return my_tag_list if my_tag is not none."""
        if self.my_tag:
            tag_names = list(self.my_tag.tags.names())
            tag_names.sort()
            return tag_names

    def get_all_tag_list(self) -> list:
        """Return all_tags corresponding to the targeted problem."""
        if self.problem:
            problem_tags = custom_models.Tag.objects.filter(problem=self.problem)
            tags_list = []
            if problem_tags:
                for problem_tag in problem_tags:
                    tags_list.extend(problem_tag.tags.names())
            all_tags_list = list(set(tags_list))
            all_tags_list.sort()
            return all_tags_list

    def get_tags(self, category: str = None, sub: str = None):
        problem_tag = custom_models.Tag.objects.all()
        if category is not None:
            problem_tag = custom_models.Tag.objects.filter(user_id=self.user_id)

        if sub is None:
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = reference_models.Psat.objects.filter(subject__abbr=sub)
            tag_id_list = problem_tag.filter(problem__psat__in=psat_list).values_list('id', flat=True)

        my_tags = taggit_models.Tag.objects.filter(
            taggit_taggeditem_items__object_id__in=tag_id_list,
            taggit_taggeditem_items__content_type=self.content_type,
        ).annotate(num_times=Count('taggit_taggeditem_items')).order_by('name')
        num_times = my_tags.values_list('num_times', flat=True)
        for my_tag in my_tags:
            weight_fun = get_weight_fun(1, 6, min(num_times), max(num_times))
            my_tag.weight = weight_fun(my_tag.num_times)
        return my_tags
