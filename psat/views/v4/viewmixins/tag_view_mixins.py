from django.contrib.contenttypes.models import ContentType
from django.db import models
from taggit.models import Tag
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import get_weight_fun

from psat import forms as psat_forms
from psat.models import psat_data_models
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Tag views."""
    model = psat_data_models.Tag
    form_class = psat_forms.TagForm
    context_object_name = 'my_tag'
    template_name = 'psat/v4/snippets/tag_container.html'

    @staticmethod
    def get_info():
        return {
            'menu': 'psat',
            'view_type': 'tag',
        }

    def get_my_tag_by_problem(self, problem):
        my_tag = self.tag_model.objects.filter(
            problem=problem, user_id=self.request.user.id).first()
        if my_tag and my_tag.tags.all():
            return my_tag

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

    def get_problem_tag_by_category(self, category):
        problem_tag = self.tag_model.objects.all()
        if category == 'my':
            problem_tag = self.tag_model.objects.filter(user_id=self.request.user.id)
        return problem_tag

    def get_tag_id_list_by_sub(self, problem_tag, sub):
        if sub is None:
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = self.psat_model.objects.filter(subject__abbr=sub)
            tag_id_list = problem_tag.filter(problem__psat__in=psat_list).values_list('id', flat=True)
        return  tag_id_list

    @staticmethod
    def get_tags_from_tag_id_list(tag_id_list):
        content_type = ContentType.objects.get(app_label='psat', model='tag')
        tags = Tag.objects.filter(
            taggit_taggeditem_items__object_id__in=tag_id_list,
            taggit_taggeditem_items__content_type=content_type,
        ).annotate(num_times=models.Count('taggit_taggeditem_items')).order_by('name')
        num_times = tags.values_list('num_times', flat=True)
        for tag in tags:
            weight_fun = get_weight_fun(1, 6, min(num_times), max(num_times))
            tag.weight = weight_fun(tag.num_times)
        return tags

    def get_tags_by_category_and_sub(self, category: str = None, sub: str = None):
        problem_tag = self.get_problem_tag_by_category(category)
        tag_id_list = self.get_tag_id_list_by_sub(problem_tag, sub)
        return self.get_tags_from_tag_id_list(tag_id_list)

    def add_tags_to_object(self, obj):
        tags = self.request.POST.get('tags', '').split(',')
        if tags:
            for tag in tags:
                tag = tag.strip()
                if tag != '':
                    obj.tags.add(tag)
