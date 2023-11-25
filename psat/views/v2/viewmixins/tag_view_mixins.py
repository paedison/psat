from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from taggit import models as taggit_models
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import get_weight_fun

from common.constants.icon_set import ConstantIconSet
from psat.forms import TagForm
from psat.models import Tag as PsatTag
from reference.models.psat_models import Psat
from reference.models.psat_models import PsatProblem
from .base_view_mixins import PsatViewInfo


class ListVariable(ConstantIconSet):
    menu = 'tag'

    def __init__(self, request, **kwargs):
        self.request = request
        self.kwargs: dict = kwargs

        self.user_id: int | None = request.user.id if request.user.is_authenticated else None

        tag_id: str = self.kwargs.get('tag_id')
        self.my_tag_id: int | None = int(tag_id) if tag_id else None
        self.my_tag = PsatTag.objects.get(id=self.my_tag_id) if self.my_tag_id else None

        problem_id: str = self.kwargs.get('problem_id')
        self.problem_id: int | None = int(problem_id) if problem_id else None

        if self.problem_id:
            self.problem = PsatProblem.objects.get(id=self.problem_id)
        if self.my_tag_id:
            self.problem = PsatProblem.objects.get(id=self.my_tag.problem_id)

        self.content_type: str = ContentType.objects.get(app_label='psat', model='tag')

    def get_my_tag_list(self) -> list | None:
        """Return my_tag_list if my_tag is not none."""
        if self.my_tag is not None:
            tag_names = list(self.my_tag.tags.names())
            tag_names.sort()
            return tag_names
        return None

    def get_all_tag_list(self) -> list:
        """Return all_tags corresponding to the targeted problem."""
        problem_tags = PsatTag.objects.filter(problem=self.problem)
        tags_list = []
        if problem_tags:
            for problem_tag in problem_tags:
                tags_list.extend(problem_tag.tags.names())
        all_tags_list = list(set(tags_list))
        all_tags_list.sort()
        return all_tags_list

    def get_tags(self, category: str = None, sub: str = None):
        problem_tag = PsatTag.objects.all()
        if category is not None:
            problem_tag = PsatTag.objects.filter(user_id=self.user_id)

        if sub is None:
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = Psat.objects.filter(subject__abbr=sub)
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


class TagViewMixIn(
    ConstantIconSet,
    PsatViewInfo,
):
    """Setting mixin for Tag views."""
    model = PsatTag
    form_class = TagForm
    context_object_name = 'my_tag'
    lookup_field = 'id'
    lookup_url_kwarg = 'tag_id'

    @staticmethod
    def get_tag_variable(request, **kwargs):
        return ListVariable(request, **kwargs)
