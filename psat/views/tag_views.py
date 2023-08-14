# Python Standard Function Import

# Django Core Import
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

# Custom App Import
from ..forms import ProblemTagForm
from ..models import ProblemTag


class TagSettingMixIn:
    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'problem_tag'
    object: any


class ProblemMyTagDetailView(TagSettingMixIn, generic.DetailView):
    template_name = 'psat/snippets/detail_tag_content.html'

    def get(self, request, *args, **kwargs) -> render:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        html = render(request, self.template_name, context)
        return html


class ProblemMyTagCreateView(TagSettingMixIn, generic.CreateView):
    template_name = 'psat/snippets/detail_tag_create.html'

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


class ProblemMyTagAddView(ProblemMyTagCreateView):
    template_name = 'psat/snippets/detail_tag_add.html'

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


class ProblemMyTagDeleteView(TagSettingMixIn, generic.DeleteView):
    @property
    def success_url(self):
        problem_tag_id = self.kwargs.get('pk', '')
        return reverse_lazy(f'psat:tag_detail', args=[problem_tag_id])

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        tag_name = self.kwargs.get('tag_name', '')
        self.object.tags.remove(tag_name)
        return HttpResponseRedirect(self.success_url)
