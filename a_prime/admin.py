from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Psat)
class PsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'is_active']
    list_filter = ['year', 'exam', 'is_active']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'ex', 'sub', 'num', 'answer']
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
