from django.contrib import admin

from psat import models


@admin.register(models.Open)
class OpenAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_id', 'ip_address', 'problem')


@admin.register(models.Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_id', 'problem', 'is_liked')


@admin.register(models.Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_id', 'problem', 'rating')


@admin.register(models.Solve)
class SolveAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_id', 'problem', 'answer', 'is_correct')


@admin.register(models.Memo)
class MemoAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'updated_at', 'user_id', 'problem', 'memo')


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'updated_at', 'user_id', 'problem', 'tag_list')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    def tag_list(self, obj):
        return ', '.join(o.name for o in obj.tags.all())


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_id', 'title', 'is_active')


@admin.register(models.CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'collection', 'problem', 'is_active')


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'updated_at', 'user', 'problem', 'title', 'hit', 'is_deleted')
