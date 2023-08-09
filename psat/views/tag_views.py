# Python Standard Function Import

# Django Core Import
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic
from taggit.models import Tag, TaggedItem

# Custom App Import
from ..forms import ProblemTagForm
from ..models import ProblemTag


class ProblemTagDetailView(generic.DetailView):
    model = ProblemTag
    context_object_name = 'problem_tag'
    template_name = 'psat/snippets/detail_tag_content.html'
    object: object

    def get(self, request, *args, **kwargs) -> render:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        html = render(request, self.template_name, context)
        return html

    def get_problem_tag(self) -> ProblemTag:
        """Get problem tag corresponding to user and problem."""
        user = self.request.user
        problem = self.object.problem
        problem_tag = None
        if user.is_authenticated:
            problem_tag = ProblemTag.objects.filter(user=user, problem=problem).first()
        return problem_tag

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        problem_tag_id = self.get_problem_tag().id
        # tags =
        return context


class ProblemTagCreateView(generic.CreateView):
    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'problem_tag'
    template_name = 'psat/snippets/detail_tag_create.html'

    def form_valid(self, form):
        self.object = form.save()
        tags = self.request.POST.get('tags', '').split(',')
        for tag in tags:
            tag = tag.strip()
            if tag != '':
                self.object.tags.add(tag)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_detail', args=[self.object.id])


class ProblemTagUpdateView(generic.UpdateView):
    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'problem_tag'
    template_name = 'psat/snippets/detail_tag_update.html'

    @property
    def tag_name(self):
        return self.kwargs.get('tag_name', '')
    
    def get_queryset(self):
        if self.tag_name:
            super().get_queryset()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        html = render(request, self.template_name, context).content.decode('utf-8')
        return JsonResponse({'html': html})

    def form_valid(self, form):
        self.object = form.save()
        tags = self.request.POST.get('tags', '').split(',')
        for tag in tags:
            tag = tag.strip()
            if tag != '':
                self.object.tags.add(tag)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_detail', args=[self.object.id])


class ProblemTagDeleteView(generic.DeleteView):
    model = ProblemTag
    form_class = ProblemTagForm
    context_object_name = 'problem_tag'

    @property
    def tag_name(self):
        return self.request.POST.get('tag_name', '')

    def get_queryset(self):
        content_type = ContentType.objects.get_for_model(ProblemTag)
        tag = Tag.objects.get(name=self.tag_name)
        pk = self.kwargs.get('pk')
        return TaggedItem.objects.get(
            object_id=pk, content_type=content_type.id, tag_id=tag.id)

    def get_success_url(self):
        return reverse_lazy(f'psat:tag_create')


# class TagEditView(View):
#     template_name = 'tag_edit.html'
#
#     def get(self, request, pk):
#         item = get_object_or_404(Problem, pk=pk)
#         tags = item.tags.all()
#
#         return render(request, self.template_name, {'item': item, 'tags': tags})
#
#     def post(self, request, pk):
#         item = get_object_or_404(Problem, pk=pk)
#
#         new_tags = request.POST.get('tags')
#         if new_tags:
#             item.tags.set(new_tags.split(','))
#
#         return redirect('tag_edit', pk=pk)
