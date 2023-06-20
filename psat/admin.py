from django.contrib import admin

from .models import Exam, Problem, Evaluation


class ExamAdmin(admin.ModelAdmin):
    list_display = ('year', 'ex', 'sub', 'exam1', 'exam2', 'subject', 'year_ex_sub')
    # list_filter = ('year', 'ex', 'sub')
    # search_fields = ('year', 'ex', 'sub')
    list_per_page = 20


class ProblemAdmin(admin.ModelAdmin):
    list_display = ('exam', 'number', 'question')
    # list_display = ('exam', 'number', 'question', 'tag_list')
    # list_filter = ('exam', 'number', 'question')
    search_fields = ('exam', 'number', 'question')
    list_per_page = 20

    # def get_queryset(self, request):
    #     return super().get_queryset(request).prefetch_related('tags')
    #
    # def tag_list(self, obj):
    #     return ', '.join(o.name for o in obj.tags.all())


class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem', 'user', 'opened_at', 'liked_at', 'rated_at',)
    # list_filter = ('problem', 'user', 'is_favorite')
    # search_fields = ('problem', 'user', 'is_favorite')
    list_per_page = 20


admin.site.register(Exam, ExamAdmin)
admin.site.register(Problem, ProblemAdmin)
admin.site.register(Evaluation, EvaluationAdmin)
