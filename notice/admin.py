# Django Core Import
from django.contrib import admin

# Custom App Import
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass
