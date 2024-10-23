from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Psat)
class PsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'order', 'is_active']
    list_filter = ['year', 'exam', 'is_active']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'subject', 'number', 'answer', 'question']
    list_filter = ['year', 'exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True


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


@admin.register(models.Lecture)
class LectureAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'subject', 'title', 'sub_title', 'youtube_id', 'order', 'created_at']
    list_filter = ['subject', 'title', 'sub_title', 'youtube_id', 'order']


@admin.register(models.LectureOpen)
class LectureOpenAdmin(ModelAdmin):
    pass


@admin.register(models.LectureLike)
class LectureLikeAdmin(ModelAdmin):
    pass


@admin.register(models.LectureMemo)
class LectureMemoAdmin(ModelAdmin):
    pass


@admin.register(models.LectureTag)
class LectureTagAdmin(ModelAdmin):
    pass


@admin.register(models.LectureTaggedItem)
class LectureTaggedItemAdmin(ModelAdmin):
    pass
