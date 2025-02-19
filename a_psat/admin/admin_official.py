from django.contrib import admin
from unfold.admin import ModelAdmin

from a_psat import models


@admin.register(models.Psat)
class PsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'order', 'is_active']
    list_filter = ['year', 'exam', 'is_active']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'ex', 'sub', 'num', 'answer', 'question']
    list_filter = ['psat__year', 'psat__exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.psat.exam}'

    @admin.display(description='과목')
    def sub(self, obj):
        return f'{obj.subject}'

    @admin.display(description='번호')
    def num(self, obj):
        return f'{obj.number}'


@admin.register(models.ProblemOpen)
class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user_id', 'reference', 'ip_address']
    fields = ['user_id', 'reference', 'ip_address']


@admin.register(models.ProblemLike)
class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fields = ['user', 'problem', 'is_liked']


@admin.register(models.ProblemRate)
class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fields = ['user', 'problem', 'rating']


@admin.register(models.ProblemSolve)
class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fields = ['user', 'problem', 'answer', 'is_correct']


@admin.register(models.ProblemMemo)
class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fields = ['user', 'problem', 'content']


@admin.register(models.ProblemTag)
class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fields = ['tag', 'slug']


@admin.register(models.ProblemTaggedItem)
class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fields = ['user', 'content_object', 'tag', 'active']


@admin.register(models.ProblemCollection)
class ProblemCollectionAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fields = ['user', 'title', 'order']


@admin.register(models.ProblemCollectionItem)
class ProblemCollectionItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fields = ['collect', 'problem', 'order']
