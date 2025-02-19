from django.contrib import admin
from unfold.admin import ModelAdmin

from a_psat import models


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
