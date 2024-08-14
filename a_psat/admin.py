from django.contrib import admin

from . import models


class LikeChoiceInline(admin.TabularInline):
    model = models.ProblemLike
    extra = 3


@admin.register(models.Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'subject', 'number', 'answer', 'question']
    list_filter = ['year', 'exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True
    fieldsets = [
        (
            None,
            {
                'fields': ['__all__'],
                'classes': ['extrapretty']
            }
        )
    ]
    exclude = ['data']
    inlines = [LikeChoiceInline]

    class Media:
        css = {'all': ['css/admin_custom.css']}


admin.site.register(models.ProblemOpen)
admin.site.register(models.ProblemLike)
admin.site.register(models.ProblemRate)
admin.site.register(models.ProblemSolve)
admin.site.register(models.ProblemMemo)
admin.site.register(models.ProblemTag)
admin.site.register(models.ProblemComment)
# admin.site.register(models.ProblemCollection)
# admin.site.register(models.ProblemCollectionItem)
