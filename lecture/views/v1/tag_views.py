import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import tag_view_mixins


class ContainerView(
    auth_mixins.LoginRequiredMixin,
    tag_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading tag container."""
    template_name = 'lecture/v1/snippets/tag_container.html'

    def get_context_data(self, **kwargs) -> dict:
        lecture_id = self.kwargs.get('lecture_id')
        lecture = self.get_lecture(lecture_id)
        my_tag = self.get_my_tag_by_lecture(lecture)
        my_tag_list = self.get_my_tag_list(my_tag)
        all_tags = self.get_all_tag_list_by_lecture(lecture)
        return super().get_context_data(
            lecture=lecture,
            my_tag=my_tag,
            my_tag_list=my_tag_list,
            all_tags=all_tags,
            icon_tag=self.ICON_TAG,
            **kwargs,
        )


class CreateView(
    auth_mixins.LoginRequiredMixin,
    tag_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    """View for creating tag."""
    template_name = 'lecture/v1/snippets/tag_container.html'

    def get_success_url(self):
        return reverse_lazy('lecture:tag_container', args=[self.lecture_id])

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user_id = self.request.user.id
        obj.lecture_id = self.lecture_id
        obj.save()
        self.add_tags_to_object(obj)
        return super().form_valid(obj)

    def get_context_data(self, **kwargs) -> dict:
        lecture = self.get_lecture(self.lecture_id)
        all_tags = self.get_all_tag_list_by_lecture(lecture)
        return super().get_context_data(
            lecture=lecture,
            all_tags=all_tags,
            icon_tag=self.ICON_TAG,
            **kwargs,
        )


class AddView(
    auth_mixins.LoginRequiredMixin,
    tag_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    """View for adding tag."""
    template_name = 'lecture/v1/snippets/tag_container.html'

    def get_success_url(self):
        return reverse_lazy('lecture:tag_container', args=[self.object.lecture_id])

    def form_valid(self, form):
        self.add_tags_to_object(self.object)
        return super().form_valid(form)


class DeleteView(
    auth_mixins.LoginRequiredMixin,
    tag_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    """View for deleting tag."""

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        success_url = reverse_lazy('lecture:tag_container', args=[obj.lecture_id])
        tag_name = self.kwargs.get('tag_name')
        obj.tags.remove(tag_name)
        if not obj.tags.all():
            obj.delete()
        return HttpResponseRedirect(success_url)


class CloudView(
    auth_mixins.LoginRequiredMixin,
    tag_view_mixins.BaseMixIn,
    vanilla.TemplateView
):
    """View for loading problem tag cloud."""
    template_name = 'lecture/v1/problem_tag_cloud.html'

    def get_context_data(self, **kwargs) -> dict:
        return super().get_context_data(
            info=self.get_info(),
            all_total_tags=self.get_tags_by_category_and_sub(),
            all_eoneo_tags=self.get_tags_by_category_and_sub(sub='언어'),
            all_jaryo_tags=self.get_tags_by_category_and_sub(sub='자료'),
            all_sanghwang_tags=self.get_tags_by_category_and_sub(sub='상황'),

            my_total_tags=self.get_tags_by_category_and_sub(category='my'),
            my_eoneo_tags=self.get_tags_by_category_and_sub(category='my', sub='언어'),
            my_jaryo_tags=self.get_tags_by_category_and_sub(category='my', sub='자료'),
            my_sanghwang_tags=self.get_tags_by_category_and_sub(category='my', sub='상황'),
            **kwargs,
        )
