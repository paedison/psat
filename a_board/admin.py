from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Notice)
class NoticeAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'user', 'title', 'created_at', 'modified_at', 'top_fixed', 'is_hidden']
    list_filter = ['top_fixed', 'is_hidden']
    save_on_top = True
    search_fields = ['title', 'content']
    show_full_result_count = True
    fields = ['user', 'title', 'content', 'top_fixed', 'is_hidden']


@admin.register(models.NoticeComment)
class NoticeCommentAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'user', 'post', 'content', 'created_at', 'modified_at']
    save_on_top = True
    search_fields = ['content']
    show_full_result_count = True
    fields = ['user', 'post', 'content']
