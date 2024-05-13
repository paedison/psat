from django.contrib import admin
from .models import lecture_models, custom_models


@admin.display(description='Subject')
def subject(obj):
    return obj.lecture.subject.name


@admin.display(description='Title')
def title(obj):
    return obj.lecture.title


@admin.display(description='Tag List')
def tag_list(obj):
    return ', '.join(o.name for o in obj.tags.all())


@admin.register(lecture_models.Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('subject', 'title', 'sub_title', 'youtube_id')


@admin.register(custom_models.Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ('user_id', subject, title, 'memo')


@admin.register(custom_models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('user_id', subject, title, tag_list)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')


@admin.register(custom_models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', subject, title, 'comment', 'hit', 'is_deleted')
