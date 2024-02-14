import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import custom_view_mixins


class TagContainerView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.TagViewMixIn,
    vanilla.TemplateView,
):
    """View for loading tag container."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#tag_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        context = super().get_context_data(**kwargs)
        context.update({
            'problem': self.problem,
            'my_tag': self.my_tag,
            'my_tag_list': self.get_my_tag_list(),
            'all_tags': self.get_all_tag_list(),
            'icon_tag': self.ICON_TAG,
        })
        return context


class TagCreateView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.TagViewMixIn,
    vanilla.CreateView,
):
    """View for creating tag."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#tag_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_properties()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form = form.save(commit=False)
        form.user_id = self.request.user.id
        response = super().form_valid(form)
        tags = self.request.POST.get('tags', '').split(',')
        for tag in tags:
            tag = tag.strip()
            if tag != '':
                self.object.tags.add(tag)
        return response

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_container', args=[self.problem_id])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update({
            'problem': self.problem,
            'all_tags': self.get_all_tag_list(),
            'icon_tag': self.ICON_TAG,
        })
        return context


class TagAddView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.TagViewMixIn,
    vanilla.UpdateView,
):
    """View for adding tag."""
    def get_success_url(self):
        return reverse_lazy(f'psat:tag_container', args=[self.object.problem_id])

    def form_valid(self, form):
        response = super().form_valid(form)
        tag = self.request.POST.get('tags')
        if tag is not None:
            self.object.tags.add(tag)
        return response


class TagDeleteView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.TagViewMixIn,
    vanilla.DeleteView,
):
    """View for deleting tag."""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy(f'psat:tag_container', args=[self.object.problem_id])
        tag_name = self.kwargs.get('tag_name')
        self.object.tags.remove(tag_name)
        return HttpResponseRedirect(success_url)


class TagCloudView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.TagViewMixIn,
    vanilla.TemplateView
):
    """View for loading problem tag cloud."""
    template_name = 'psat/v4/problem_tag_cloud.html'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()
        context = super().get_context_data(**kwargs)
        context.update({
            'info': self.info,
            'all_total_tags': self.get_tags(),
            'all_eoneo_tags': self.get_tags(sub='언어'),
            'all_jaryo_tags': self.get_tags(sub='자료'),
            'all_sanghwang_tags': self.get_tags(sub='상황'),

            'my_total_tags': self.get_tags(category='my'),
            'my_eoneo_tags': self.get_tags(category='my', sub='언어'),
            'my_jaryo_tags': self.get_tags(category='my', sub='자료'),
            'my_sanghwang_tags': self.get_tags(category='my', sub='상황'),
        })
        return context


container_view = TagContainerView.as_view()
create_view = TagCreateView.as_view()
add_view = TagAddView.as_view()
delete_view = TagDeleteView.as_view()
cloud_view = TagCloudView.as_view()
