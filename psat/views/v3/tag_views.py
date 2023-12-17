import vanilla
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import custom_view_mixins


class TagContainerView(
    custom_view_mixins.TagViewMixIn,
    vanilla.TemplateView,
):
    """View for loading problem tag container."""
    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'my_tag': self.my_tag,
            'my_tag_list': self.get_my_tag_list(),
            'all_tags': self.get_all_tag_list(),
            'problem': self.problem,
            'icon_tag': self.ICON_TAG,
        }


class TagCreateView(
    custom_view_mixins.TagViewMixIn,
    vanilla.CreateView,
):
    """View for creating problem tag."""
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
        self.get_properties()

        return {
            'all_tags': self.get_all_tag_list(),
            'problem': self.problem,
            'icon_tag': self.ICON_TAG,
        }


class TagAddView(
    custom_view_mixins.TagViewMixIn,
    vanilla.UpdateView,
):
    """View for adding problem tag."""
    def get_success_url(self):
        return reverse_lazy(f'psat:tag_container', args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        tag = self.request.POST.get('tags')
        if tag is not None:
            self.object.tags.add(tag)
        return response


class TagDeleteView(
    custom_view_mixins.TagViewMixIn,
    vanilla.DeleteView,
):
    """View for deleting problem tag."""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy(f'psat:tag_container', args=[self.object.id])
        tag_name = self.kwargs.get('tag_name')
        self.object.tags.remove(tag_name)

        return HttpResponseRedirect(success_url)


class TagCloudView(
    custom_view_mixins.TagViewMixIn,
    vanilla.TemplateView
):
    """View for loading problem tag cloud."""
    template_name = 'psat/v3/problem_tag_cloud.html'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'info': self.info,
            'all_total_tags': self.get_tags(),
            'all_eoneo_tags': self.get_tags(sub='언어'),
            'all_jaryo_tags': self.get_tags(sub='자료'),
            'all_sanghwang_tags': self.get_tags(sub='상황'),

            'my_total_tags': self.get_tags(category='my'),
            'my_eoneo_tags': self.get_tags(category='my', sub='언어'),
            'my_jaryo_tags': self.get_tags(category='my', sub='자료'),
            'my_sanghwang_tags': self.get_tags(category='my', sub='상황'),
        }


container_view = TagContainerView.as_view()
create_view = TagCreateView.as_view()
add_view = TagAddView.as_view()
delete_view = TagDeleteView.as_view()
cloud_view = TagCloudView.as_view()
