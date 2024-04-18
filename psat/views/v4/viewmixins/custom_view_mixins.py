from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from taggit import models as taggit_models
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import get_weight_fun

from common.constants.icon_set import ConstantIconSet
from dashboard.models import psat_data_models
from psat import forms, models, utils
from reference.models import psat_models


class BaseMixIn(ConstantIconSet):
    request: any
    kwargs: dict

    problem_model = psat_models.PsatProblem

    like_model = models.Like
    rate_model = models.Rate
    solve_model = models.Solve

    like_log_model = psat_data_models.PsatLikeLog
    rate_log_model = psat_data_models.PsatRateLog
    solve_log_model = psat_data_models.PsatSolveLog

    @staticmethod
    def get_url(name, *args):
        return utils.get_url(name, *args)

    def invert_post_variable_by_bool(self, variable: str):
        post_variable = self.request.POST.get(variable, '')
        if post_variable == '':
            return ''
        else:
            post_variable_dict = {'True': True, 'False': False, 'None': False}
            return not post_variable_dict[post_variable]

    def get_post_variable_by_integer(self, variable: str):
        post_variable = self.request.POST.get(variable, '')
        if post_variable == '':
            return ''
        else:
            return int(post_variable)

    def get_problem_by_problem_id(self, problem_id):
        return (
            self.problem_model.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .get(id=problem_id)
        )


class CustomUpdateViewMixIn(BaseMixIn):
    """Represent PSAT custom data update view mixin."""

    @staticmethod
    def get_option_name(view_type) -> str:
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        return option_dict[view_type]

    def get_find_filter_by_problem_id(self, problem_id) -> dict:
        user_id = self.request.user.id
        find_filter = {
            'problem_id': problem_id,
            'user_id': user_id,
        }
        if not user_id:
            find_filter['ip_address'] = self.request.META.get('REMOTE_ADDR')
        return find_filter

    def get_filter_dict_by_problem_id(self, view_type, problem_id):
        problem = self.get_problem_by_problem_id(problem_id)
        find_filter = self.get_find_filter_by_problem_id(problem_id)

        is_liked = self.invert_post_variable_by_bool('is_liked')
        rating = self.get_post_variable_by_integer('rating')
        answer = self.get_post_variable_by_integer('answer')
        is_correct = answer == problem.answer

        update_filter_expr = {
            'problem': {},
            'like': {'is_liked': is_liked},
            'rate': {'rating': rating},
            'solve': {
                'answer': answer,
                'is_correct': is_correct,
            },
        }
        update_filter = update_filter_expr[view_type]

        create_filter = find_filter.copy()
        create_filter.update(update_filter)

        return {
            'find': find_filter,
            'update': update_filter,
            'create': create_filter,
        }

    def get_data_instance_by_filter_dict(self, view_type, filter_dict):
        model_dict = {
            'like': self.like_model,
            'rate': self.rate_model,
            'solve': self.solve_model,
        }
        data_model = model_dict[view_type]

        find_filter = filter_dict['find']
        update_filter = filter_dict['update']
        create_filter = filter_dict['create']
        if data_model:
            try:
                instance = data_model.objects.get(**find_filter)
                for key, item in update_filter.items():
                    setattr(instance, key, item)
                instance.save()
            except data_model.DoesNotExist:
                instance = data_model.objects.create(**create_filter)
            return instance

    def make_log_instance_by_filter_dict(
            self, view_type, data_instance, filter_dict
    ):
        find_filter = filter_dict['find']
        create_filter = filter_dict['create']
        if data_instance:
            log_model_dict = {
                'like': self.like_log_model,
                'rate': self.rate_log_model,
                'solve': self.solve_log_model,
            }
            log_model = log_model_dict[view_type]
            data_id = data_instance.id
            recent_log = log_model.objects.filter(**find_filter).order_by('-id').first()
            repetition = recent_log.repetition + 1 if recent_log else 1
            create_filter.update(
                {'repetition': repetition, 'data_id': data_id}
            )
            log_model.objects.create(**create_filter)


class MemoViewMixIn(BaseMixIn):
    """Setting mixin for Memo views."""
    model = models.Memo
    form_class = forms.MemoForm
    context_object_name = 'my_memo'
    template_name = 'psat/v4/snippets/memo_container.html'

    memo_model = models.Memo

    def get_my_memo_by_problem(self, problem):
        return self.memo_model.objects.filter(
            problem=problem, user_id=self.request.user.id).first()


class TagViewMixIn(BaseMixIn):
    """Setting mixin for Tag views."""
    menu = 'tag'
    model = models.Tag
    form_class = forms.TagForm
    context_object_name = 'my_tag'
    template_name = 'psat/v4/snippets/tag_container.html'

    tag_model = models.Tag
    psat_model = psat_models.Psat
    problem_model = psat_models.PsatProblem

    @staticmethod
    def get_info():
        return {
            'menu': 'psat',
            'view_type': 'tag',
        }

    def get_my_tag_by_problem(self, problem):
        return self.tag_model.objects.filter(
            problem=problem, user_id=self.request.user.id).first()

    @staticmethod
    def get_my_tag_list(my_tag) -> list | None:
        """Return my_tag_list if my_tag is not none."""
        if my_tag:
            tag_names = list(my_tag.tags.names())
            tag_names.sort()
            return tag_names

    def get_all_tag_list_by_problem(self, problem) -> list:
        """Return all_tags corresponding to the targeted problem."""
        if problem:
            problem_tags = self.tag_model.objects.filter(problem=problem)
            tags_list = []
            if problem_tags:
                for problem_tag in problem_tags:
                    tags_list.extend(problem_tag.tags.names())
            all_tags_list = list(set(tags_list))
            all_tags_list.sort()
            return all_tags_list

    def get_tags_by_category_and_sub(self, category: str = None, sub: str = None):
        content_type = ContentType.objects.get(app_label='psat', model='tag')
        problem_tag = self.tag_model.objects.all()
        if category is not None:
            problem_tag = self.tag_model.objects.filter(user_id=self.request.user.id)

        if sub is None:
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = self.psat_model.objects.filter(subject__abbr=sub)
            tag_id_list = problem_tag.filter(problem__psat__in=psat_list).values_list('id', flat=True)

        my_tags = taggit_models.Tag.objects.filter(
            taggit_taggeditem_items__object_id__in=tag_id_list,
            taggit_taggeditem_items__content_type=content_type,
        ).annotate(num_times=Count('taggit_taggeditem_items')).order_by('name')
        num_times = my_tags.values_list('num_times', flat=True)
        for my_tag in my_tags:
            weight_fun = get_weight_fun(1, 6, min(num_times), max(num_times))
            my_tag.weight = weight_fun(my_tag.num_times)
        return my_tags

    def add_tags_to_object(self, obj):
        tags = self.request.POST.get('tags', '').split(',')
        if tags:
            for tag in tags:
                tag = tag.strip()
                if tag != '':
                    obj.tags.add(tag)
