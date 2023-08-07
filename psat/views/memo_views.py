# Python Standard Function Import

# Django Core Import
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

# Custom App Import
from ..forms import ProblemMemoForm
from ..models import ProblemMemo


class MemoDetailView(generic.DetailView):
    model = ProblemMemo
    context_object_name = 'problem_memo'
    template_name = 'psat/snippets/detail_memo_content.html'
    object: object

    def get(self, request, *args, **kwargs) -> render:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        html = render(request, self.template_name, context)
        return html


class MemoCreateView(generic.CreateView):
    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'
    template_name = 'psat/snippets/detail_memo_create.html'

    def get_success_url(self):
        return reverse_lazy(f'psat:memo_detail', args=[self.object.id])


class MemoUpdateView(generic.UpdateView):
    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'
    template_name = 'psat/snippets/detail_memo_update.html'
    object: object

    def get_success_url(self):
        return reverse_lazy(f'psat:memo_detail', args=[self.object.id])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        html = render(request, self.template_name, context).content.decode('utf-8')
        return JsonResponse({'html': html})


class MemoDeleteView(generic.DeleteView):
    model = ProblemMemo
    form_class = ProblemMemoForm
    context_object_name = 'problem_memo'

    def get_success_url(self):
        return reverse_lazy(f'psat:memo_create')
