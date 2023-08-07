from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from ..models import Problem
from taggit.models import Tag


class TagEditView(View):
    template_name = 'tag_edit.html'

    def get(self, request, pk):
        item = get_object_or_404(Problem, pk=pk)
        tags = item.tags.all()

        return render(request, self.template_name, {'item': item, 'tags': tags})

    def post(self, request, pk):
        item = get_object_or_404(Problem, pk=pk)

        new_tags = request.POST.get('tags')
        if new_tags:
            item.tags.set(new_tags.split(','))

        return redirect('tag_edit', pk=pk)
