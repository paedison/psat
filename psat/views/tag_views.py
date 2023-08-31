# Python Standard Function Import

# Django Core Import
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic
from vanilla import DetailView

# Custom App Import
from ..forms import ProblemTagForm
from ..models import ProblemTag, Problem


class TagSettingMixIn:
    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'my_tag'
    object: any


class ProblemTagDetailView(TagSettingMixIn, DetailView):
    template_name = 'psat/snippets/detail_tag_container.html'

    def get_all_tags(self) -> list:
        problem = self.object.problem
        problem_tags = ProblemTag.objects.filter(problem=problem)
        tags = []
        for tag in problem_tags:
            tag_name = tag.tags.names()
            tags.extend(tag_name)
        all_tags = list(set(tags))
        all_tags.sort()
        return all_tags

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['my_tag'] = self.object
        context['my_tag_list'] = list(self.object.tags.names())
        context['all_tag'] = self.get_all_tags()
        context['problem'] = self.object.problem
        return context


class ProblemTagCreateView(TagSettingMixIn, generic.CreateView):
    template_name = 'psat/snippets/detail_tag_container.html#create'
    my_tag: any
    problem: Problem

    @property
    def problem(self) -> Problem:
        problem_id = self.request.POST.get('problem', '')
        return Problem.objects.filter(id=problem_id).first()

    def post(self, request, *args, **kwargs):
        user = self.request.user
        my_tag = None
        if self.problem:
            my_tag = ProblemTag.objects.filter(
                user=user, problem=self.problem).first()
        if my_tag:
            self.object = my_tag
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        tags = self.request.POST.get('tags', '').split(',')
        for tag in tags:
            tag = tag.strip()
            if tag != '':
                self.object.tags.add(tag)
        return response

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_detail', args=[self.object.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['problem'] = self.problem
        return context


class ProblemTagAddView(ProblemTagCreateView):
    template_name = 'psat/snippets/detail_tag_container.html#add'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ProblemTagDeleteView(TagSettingMixIn, generic.DeleteView):
    @property
    def success_url(self):
        my_tag_id = self.kwargs.get('pk', '')
        return reverse_lazy(f'psat:tag_detail', args=[my_tag_id])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        tag_name = self.kwargs.get('tag_name', '')
        self.object.tags.remove(tag_name)
        return HttpResponseRedirect(self.success_url)


problem_tag_create_view = ProblemTagCreateView.as_view()
problem_tag_detail_view = ProblemTagDetailView.as_view()
problem_tag_add_view = ProblemTagAddView.as_view()
problem_tag_delete_view = ProblemTagDeleteView.as_view()
