from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from taggit.models import Tag
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import get_weight_fun
from vanilla import DetailView, TemplateView, CreateView, DeleteView, UpdateView

from common.constants import icon, color
from ..forms import ProblemTagForm
from ..models import ProblemTag, Problem, Exam


class TagSettingMixIn:
    """Setting mixin for Tag views."""
    kwargs: dict
    object: ProblemTag

    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'my_tag'
    lookup_field = 'id'
    lookup_url_kwarg = 'tag_id'

    @property
    def my_tag_id(self) -> int | None:
        """Get my_tag_id in case of tag_container, tag_add, tag_delete."""
        tag_id = self.kwargs.get('tag_id')
        return int(tag_id) if tag_id else None

    @property
    def my_tag(self) -> ProblemTag | None:
        """Return my_tag field in the ProblemTag model if my_tag_id exists."""
        return ProblemTag.objects.get(id=self.my_tag_id) if self.my_tag_id else None

    @property
    def problem_id(self) -> int | None:
        """Get problem_id in case of tag_create."""
        problem_id = self.kwargs.get('problem_id')
        return int(problem_id) if problem_id else None

    @property
    def problem(self) -> Problem | None:
        """Return problem in the Problem model if problem_id exists."""
        if self.problem_id:
            return Problem.objects.get(id=self.problem_id)
        if self.my_tag_id:
            return Problem.objects.get(id=self.my_tag.problem_id)

    @property
    def my_tag_list(self) -> list | None:
        """Return my_tag_list if my_tag is not none."""
        if self.my_tag is not None:
            tag_names = list(self.my_tag.tags.names())
            tag_names.sort()
            return tag_names
        return None

    @property
    def all_tags(self) -> list:
        """Return all_tags corresponding to the targeted problem."""
        problem_tags = ProblemTag.objects.filter(problem=self.problem)
        tags_list = []
        if problem_tags:
            for problem_tag in problem_tags:
                tags_list.extend(problem_tag.tags.names())
        all_tags_list = list(set(tags_list))
        all_tags_list.sort()
        return all_tags_list


class ProblemTagContainerView(TagSettingMixIn, DetailView):
    """View for loading problem tag container."""
    template_name = 'psat/snippets/detail_tag_container.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['my_tag'] = self.object
        context['my_tag_list'] = self.my_tag_list
        context['all_tags'] = self.all_tags
        context['problem'] = self.problem
        return context


class ProblemTagCreateView(TagSettingMixIn, CreateView):
    """View for creating problem tag."""
    template_name = 'psat/snippets/detail_tag_create.html'

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_container', args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        tags = self.request.POST.get('tags', '').split(',')
        for tag in tags:
            tag = tag.strip()
            if tag != '':
                self.object.tags.add(tag)
        return response

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        context['all_tags'] = self.all_tags
        return context


class ProblemTagAddView(TagSettingMixIn, UpdateView):
    """View for adding problem tag."""
    template_name = 'psat/snippets/detail_tag_container.html'

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_container', args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        tag = self.request.POST.get('tags')
        if tag is not None:
            self.object.tags.add(tag)
        return response

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        context['all_tags'] = self.all_tags
        return context


class ProblemTagDeleteView(TagSettingMixIn, DeleteView):
    """View for deleting problem tag."""

    @property
    def tag_name(self) -> str:
        """Return tag_name for deleting."""
        return self.kwargs.get('tag_name')

    @property
    def success_url(self) -> reverse_lazy:
        """Return success_url 'before' deleting the tag."""
        return reverse_lazy(f'psat:tag_container', args=[self.object.id])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.tags.remove(self.tag_name)
        return HttpResponseRedirect(self.success_url)


class ProblemTagCloudView(TagSettingMixIn, TemplateView):
    """View for loading problem tag cloud."""
    template_name = 'psat/problem_tag_cloud.html'

    @property
    def info(self):
        return {
            'menu': 'tag',
            # 'category': self.category,
            'view_type': 'tag',
            'type': f'tagCloudList',
            'title': 'Tag Cloud',
            # 'sub': self.url['sub'],
            # 'sub_code': self.url['sub_code'],
            # 'pagination_url': self.pagination_url,
            # 'target_id': f'{self.view_type}ListContent{self.url["sub_code"]}',
            'icon': icon.MENU_ICON_SET['tag'],
            'color': color.COLOR_SET['tag'],
        }

    @property
    def content_type(self) -> ContentType:
        return ContentType.objects.get(app_label='psat', model='problemtag')

    def get_tags(self, category: str = None, sub: str = None) -> Tag:
        if category is None:
            problem_tag = ProblemTag.objects.all()
        else:
            problem_tag = ProblemTag.objects.filter(user=self.request.user)

        if sub is None:
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            exam_list = Exam.objects.filter(sub=sub)
            tag_id_list = problem_tag.filter(problem__exam__in=exam_list).values_list('id', flat=True)

        my_tags = Tag.objects.filter(
            taggit_taggeditem_items__object_id__in=tag_id_list,
            taggit_taggeditem_items__content_type=self.content_type,
        ).annotate(num_times=Count('taggit_taggeditem_items')).order_by('name')
        num_times = my_tags.values_list('num_times', flat=True)
        for my_tag in my_tags:
            weight_fun = get_weight_fun(1, 6, min(num_times), max(num_times))
            my_tag.weight = weight_fun(my_tag.num_times)
        return my_tags

    def get_my_tags(self, sub: str) -> Tag:
        problem_tag = ProblemTag.objects.filter(user=self.request.user)
        if sub == '':
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            exam_list = Exam.objects.filter(sub=sub)
            tag_id_list = problem_tag.filter(problem__exam__in=exam_list).values_list('id', flat=True)
        return self.get_tags(tag_id_list)

    def get_all_tags(self, sub: str) -> Tag:
        problem_tag = ProblemTag.objects.all()
        if sub == '':
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            exam_list = Exam.objects.filter(sub=sub)
            tag_id_list = problem_tag.filter(problem__exam__in=exam_list).values_list('id', flat=True)
        return self.get_tags(tag_id_list)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        context['total_all_tags'] = self.get_tags()
        context['eoneo_all_tags'] = self.get_tags(sub='언어')
        context['jaryo_all_tags'] = self.get_tags(sub='자료')
        context['sanghwang_all_tags'] = self.get_tags(sub='상황')

        context['total_my_tags'] = self.get_tags(category='my')
        context['eoneo_my_tags'] = self.get_tags(category='my', sub='언어')
        context['jaryo_my_tags'] = self.get_tags(category='my', sub='자료')
        context['sanghwang_my_tags'] = self.get_tags(category='my', sub='상황')

        context['info'] = self.info
        return context


problem_tag_container_view = ProblemTagContainerView.as_view()
problem_tag_create_view = ProblemTagCreateView.as_view()
problem_tag_add_view = ProblemTagAddView.as_view()
problem_tag_delete_view = ProblemTagDeleteView.as_view()
problem_tag_cloud_view = ProblemTagCloudView.as_view()
