from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from vanilla import TemplateView, CreateView, DeleteView, UpdateView

from .viewmixins.tag_view_mixins import TagViewMixIn


class TagContainerView(TagViewMixIn, TemplateView):
    """View for loading problem tag container."""
    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = self.get_tag_variable(self.request, **self.kwargs)
        return {
            'my_tag': variable.my_tag,
            'my_tag_list': variable.get_my_tag_list(),
            'all_tags': variable.get_all_tag_list(),
            'problem': variable.problem,
            'icon_tag': variable.ICON_TAG,
        }


class TagCreateView(TagViewMixIn, CreateView):
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
        variable = self.get_tag_variable(self.request, **self.kwargs)
        return {
            'all_tags': variable.get_all_tag_list(),
            'problem': variable.problem,
            'icon_tag': variable.ICON_TAG,
        }


class TagAddView(TagViewMixIn, UpdateView):
    """View for adding problem tag."""
    def get_success_url(self):
        return reverse_lazy(f'psat:tag_container', args=[self.object.id])

    def form_valid(self, form):
        response = super().form_valid(form)
        tag = self.request.POST.get('tags')
        if tag is not None:
            self.object.tags.add(tag)
        return response


class TagDeleteView(TagViewMixIn, DeleteView):
    """View for deleting problem tag."""

    @property
    def tag_name(self) -> str:
        """Return tag_name for deleting."""
        return self.kwargs.get('tag_name')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy(f'psat:tag_container', args=[self.object.id])
        self.object.tags.remove(self.tag_name)
        return HttpResponseRedirect(success_url)


class TagCloudView(TagViewMixIn, TemplateView):
    """View for loading problem tag cloud."""
    template_name = 'psat/v2/problem_tag_cloud.html'

    def get_context_data(self, **kwargs) -> dict:
        variable = self.get_tag_variable(self.request, **self.kwargs)

        return {
            'info': variable.get_info(),
            'all_total_tags': variable.get_tags(),
            'all_eoneo_tags': variable.get_tags(sub='언어'),
            'all_jaryo_tags': variable.get_tags(sub='자료'),
            'all_sanghwang_tags': variable.get_tags(sub='상황'),

            'my_total_tags': variable.get_tags(category='my'),
            'my_eoneo_tags': variable.get_tags(category='my', sub='언어'),
            'my_jaryo_tags': variable.get_tags(category='my', sub='자료'),
            'my_sanghwang_tags': variable.get_tags(category='my', sub='상황'),
        }


container_view = TagContainerView.as_view()
create_view = TagCreateView.as_view()
add_view = TagAddView.as_view()
delete_view = TagDeleteView.as_view()
cloud_view = TagCloudView.as_view()
