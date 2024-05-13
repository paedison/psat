import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.urls import reverse_lazy

from psat import utils
from .viewmixins import memo_view_mixins


class ContainerView(
    auth_mixins.LoginRequiredMixin,
    memo_view_mixins.BaseMixIn,
    vanilla.TemplateView,
):
    """View for loading memo container."""
    template_name = 'lecture/v1/snippets/memo_container.html'

    def get_context_data(self, **kwargs):
        lecture = self.get_lecture(self.lecture_id)
        my_memo = self.get_my_memo_by_lecture(lecture)
        return super().get_context_data(
            form=self.form_class,
            lecture_id=self.lecture_id,
            lecture=lecture,
            my_memo=my_memo,
            icon_memo=self.ICON_MEMO,
            icon_board=self.ICON_BOARD,
            **kwargs,
        )


class CreateView(
    auth_mixins.LoginRequiredMixin,
    memo_view_mixins.BaseMixIn,
    vanilla.CreateView,
):
    """View for creating memo."""
    template_name = 'lecture/v1/snippets/memo_container.html#create_form'

    def form_valid(self, form):
        form = form.save(commit=False)
        form.user_id = self.request.user.id
        form.lecture_id = self.lecture_id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('lecture:memo_container', args=[self.lecture_id])

    def get_context_data(self, **kwargs):
        lecture = self.get_lecture(self.lecture_id)
        return super().get_context_data(
            lecture=lecture,
            icon_board=self.ICON_BOARD,
            icon_memo=self.ICON_MEMO,
            **kwargs,
        )


class UpdateView(
    auth_mixins.LoginRequiredMixin,
    memo_view_mixins.BaseMixIn,
    vanilla.UpdateView,
):
    """View for updating memo."""
    template_name = 'lecture/v1/snippets/memo_container.html#update_form'

    def get_success_url(self):
        return reverse_lazy('lecture:memo_container', args=[self.object.lecture_id])

    def get_context_data(self, **kwargs):
        lecture = self.get_lecture(self.lecture_id)
        return super().get_context_data(
            lecture=lecture,
            icon_board=self.ICON_BOARD,
            icon_memo=self.ICON_MEMO,
            **kwargs,
        )


class DeleteView(
    auth_mixins.LoginRequiredMixin,
    memo_view_mixins.BaseMixIn,
    vanilla.DeleteView,
):
    """View for deleting memo."""
    template_name = 'lecture/v1/snippets/memo_container.html'

    def get_success_url(self):
        lecture_id = self.request.POST.get('lecture_id')
        return reverse_lazy('lecture:memo_container', args=[lecture_id])
