import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import custom_view_mixins


class MemoContainerView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.MemoViewMixIn,
    vanilla.TemplateView,
):
    """View for loading memo container."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#memo_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_context_data(self, **kwargs):
        self.get_properties()
        context = super().get_context_data(**kwargs)
        form = self.form_class()
        context.update({
            'form': form,
            'problem': self.problem,
            'my_memo': self.my_memo,
            'icon_memo': self.ICON_MEMO,
            'icon_board': self.ICON_BOARD,
        })
        return context


class MemoCreateView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.MemoViewMixIn,
    vanilla.CreateView,
):
    """View for creating memo."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#memo_main',
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
        form.user_id = self.user_id
        form.problem_id = self.problem_id
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('psat:memo_container', args=[self.problem_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'problem': self.problem,
            'icon_board': self.ICON_BOARD,
            'icon_memo': self.ICON_MEMO,
        })
        return context


class MemoUpdateView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.MemoViewMixIn,
    vanilla.UpdateView,
):
    """View for updating memo."""

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#memo_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_success_url(self):
        return reverse_lazy('psat:memo_container', args=[self.object.problem_id])

    def get_context_data(self, **kwargs):
        self.get_properties()
        context = super().get_context_data(**kwargs)
        context.update({
            'problem': self.problem,
            'update': True,
            'icon_board': self.ICON_BOARD,
            'icon_memo': self.ICON_MEMO,
        })
        return context


class MemoDeleteView(
    auth_mixins.LoginRequiredMixin,
    custom_view_mixins.MemoViewMixIn,
    vanilla.DeleteView,
):
    """View for deleting memo."""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse_lazy('psat:memo_container', args=[self.object.problem_id])
        self.object.delete()
        return HttpResponseRedirect(success_url)


container_view = MemoContainerView.as_view()
create_view = MemoCreateView.as_view()
update_view = MemoUpdateView.as_view()
delete_view = MemoDeleteView.as_view()
