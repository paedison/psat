from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'subject', 'number', 'answer', 'question']
    list_filter = ['year', 'exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    class Media:
        css = {'all': ['css/admin_custom.css']}


@admin.register(models.ProblemOpen)
class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'ip_address']
    fields = ['user', 'reference', 'ip_address', 'remarks']


@admin.register(models.ProblemLike)
class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fields = ['user', 'problem', 'is_liked', 'remarks']


@admin.register(models.ProblemRate)
class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fields = ['user', 'problem', 'rating', 'remarks']


@admin.register(models.ProblemSolve)
class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fields = ['user', 'problem', 'answer', 'is_correct', 'remarks']


@admin.register(models.ProblemMemo)
class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fields = ['user', 'problem', 'content', 'remarks']


@admin.register(models.ProblemTag)
class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fields = ['tag', 'slug']


@admin.register(models.ProblemTaggedItem)
class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fields = ['user', 'content_object', 'tag', 'active', 'remarks']


@admin.register(models.ProblemCollection)
class ProblemCollectionAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fields = ['user', 'title', 'order']


@admin.register(models.ProblemCollectionItem)
class ProblemCollectionItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fields = ['collect', 'problem', 'order', 'remarks']


# admin.site.register(models.ProblemOpen)
# admin.site.register(models.ProblemLike)
# admin.site.register(models.ProblemRate)
# admin.site.register(models.ProblemSolve)
# admin.site.register(models.ProblemMemo)
# admin.site.register(models.ProblemTag)
# admin.site.register(models.ProblemComment)
# admin.site.register(models.ProblemCollection)
# admin.site.register(models.ProblemCollectionItem)
