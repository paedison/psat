# Python Standard Function Import

# Django Core Import
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

# Custom App Import
from ..forms import ProblemTagForm
from ..models import ProblemTag, Problem


class TagSettingMixIn:
    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'my_tag'
    object: any


class ProblemTagDetailView(TagSettingMixIn, generic.DetailView):
    template_name = 'psat/snippets/detail_tag_container.html'

    def get(self, request, *args, **kwargs) -> render:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        html = render(request, self.template_name, context)
        return html

    def get_all_tags(self) -> list:
        """Get problem all tags corresponding to the problem."""
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

    def get_problem(self) -> Problem:
        problem_id = self.request.POST.get('problem', '')
        problem = Problem.objects.filter(id=problem_id).first()
        return problem

    def post(self, request, *args, **kwargs):
        user = self.request.user
        my_tag = None
        problem = self.get_problem()

        if problem:
            my_tag = ProblemTag.objects.filter(
                user=user, problem=problem).first()
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
        problem = self.get_problem()
        context['problem'] = problem
        return context


class ProblemTagAddView(ProblemTagCreateView):
    template_name = 'psat/snippets/detail_tag_container.html#add'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        html = render(request, self.template_name, context).content.decode('utf-8')
        return JsonResponse({'html': html})

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
