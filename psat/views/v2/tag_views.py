from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from taggit.models import Tag
from taggit_templatetags2.templatetags.taggit_templatetags2_tags import get_weight_fun
from vanilla import DetailView, TemplateView, CreateView, DeleteView, UpdateView

from common import constants
from psat.models import Tag
from .viewmixins import TagViewMixIn
from reference.models import Psat


class TagContainerView(TagViewMixIn, DetailView):
    """View for loading problem tag container."""
    template_name = 'psat/v2/snippets/tag_container.html'

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['my_tag'] = self.object
        context['my_tag_list'] = self.my_tag_list
        context['all_tags'] = self.all_tags
        context['problem'] = self.problem
        return context


class TagCreateView(TagViewMixIn, CreateView):
    """View for creating problem tag."""
    template_name = 'psat/v2/snippets/tag_create.html'

    def get_success_url(self):
        return reverse_lazy(f'psat_v2:tag_container', args=[self.object.id])

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
        context['all_tags'] = self.all_tags
        context['problem'] = self.problem
        return context


class TagAddView(TagViewMixIn, UpdateView):
    """View for adding problem tag."""
    template_name = 'psat/v2/snippets/tag_container.html'

    def get_success_url(self):
        return reverse_lazy(f'psat_v2:tag_container', args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        tag = self.request.POST.get('tags')
        if tag is not None:
            self.object.tags.add(tag)
        return response

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['all_tags'] = self.all_tags
        context['problem'] = self.problem
        return context


class TagDeleteView(TagViewMixIn, DeleteView):
    """View for deleting problem tag."""

    @property
    def tag_name(self) -> str:
        """Return tag_name for deleting."""
        return self.kwargs.get('tag_name')

    @property
    def success_url(self):
        """Return success_url 'before' deleting the tag."""
        return reverse_lazy(f'psat_v2:tag_container', args=[self.object.id])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.tags.remove(self.tag_name)
        return HttpResponseRedirect(self.success_url)


class TagCloudView(TagViewMixIn, TemplateView):
    """View for loading problem tag cloud."""
    template_name = 'psat/v2/problem_tag_cloud.html'

    @property
    def info(self):
        return {
            'menu': self.menu,
            'view_type': 'tag',
            'type': f'tagCloudList',
            'title': 'Tag Cloud',
            'icon': constants.icon.MENU_ICON_SET['tag'],
        }

    @property
    def content_type(self) -> ContentType:
        return ContentType.objects.get(app_label='psat', model='tag')

    def get_tags(self, category: str = None, sub: str = None) -> Tag:
        if category is None:
            problem_tag = Tag.objects.all()
        else:
            problem_tag = Tag.objects.filter(user_id=self.user_id)

        if sub is None:
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = Psat.objects.filter(subject__abbr=sub)
            tag_id_list = problem_tag.filter(problem__psat__in=psat_list).values_list('id', flat=True)

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
        problem_tag = Tag.objects.filter(user_id=self.user_id)
        if sub == '':
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = Psat.objects.filter(subject__abbr=sub)
            tag_id_list = problem_tag.filter(problem__psat__in=psat_list).values_list('id', flat=True)
        return self.get_tags(tag_id_list)

    def get_all_tags(self, sub: str) -> Tag:
        problem_tag = Tag.objects.all()
        if sub == '':
            tag_id_list = problem_tag.values_list('id', flat=True)
        else:
            psat_list = Psat.objects.filter(subject__abbr=sub)
            tag_id_list = problem_tag.filter(problem__psat__in=psat_list).values_list('id', flat=True)
        return self.get_tags(tag_id_list)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        context['all_total_tags'] = self.get_tags()
        context['all_eoneo_tags'] = self.get_tags(sub='언어')
        context['all_jaryo_tags'] = self.get_tags(sub='자료')
        context['all_sanghwang_tags'] = self.get_tags(sub='상황')

        context['my_total_tags'] = self.get_tags(category='my')
        context['my_eoneo_tags'] = self.get_tags(category='my', sub='언어')
        context['my_jaryo_tags'] = self.get_tags(category='my', sub='자료')
        context['my_sanghwang_tags'] = self.get_tags(category='my', sub='상황')

        context['info'] = self.info
        return context


container_view = TagContainerView.as_view()
create_view = TagCreateView.as_view()
add_view = TagAddView.as_view()
delete_view = TagDeleteView.as_view()
cloud_view = TagCloudView.as_view()
