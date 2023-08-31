# Python Standard Function Import

# Django Core Import
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

# Custom App Import
from ..forms import ProblemMemoForm
from ..models import ProblemMemo


class ProblemMemoDetailView(generic.DetailView):
    model = ProblemMemo
    context_object_name = 'problem_memo'
    template_name = 'psat/snippets/detail_memo_container.html#content'
    object: object

    def get(self, request, *args, **kwargs) -> render:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        html = render(request, self.template_name, context)
        return html


class ProblemMemoCreateView(generic.CreateView):
    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'
    template_name = 'psat/snippets/detail_memo_container.html#create'

    def get_success_url(self):
        return reverse_lazy(f'psat:memo_detail', args=[self.object.id])


class ProblemMemoUpdateView(generic.UpdateView):
    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'
    template_name = 'psat/snippets/detail_memo_container.html#update'
    object: object

    def get_success_url(self):
        return reverse_lazy(f'psat:memo_detail', args=[self.object.id])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)


class ProblemMemoDeleteView(generic.DeleteView):
    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'

    def get_success_url(self):
        return reverse_lazy(f'psat:memo_create')


problem_memo_create_view = ProblemMemoCreateView.as_view()
problem_memo_detail_view = ProblemMemoDetailView.as_view()
problem_memo_update_view = ProblemMemoUpdateView.as_view()
problem_memo_delete_view = ProblemMemoDeleteView.as_view()
