from django.contrib import admin

from .models import (
    PrimePsatExam, PrimePsatStudent, PrimePsatRegisteredStudent, PrimePsatAnswerCount,
)


@admin.register(PrimePsatExam)
class PrimePsatExamAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id',
        'page_opened_at', 'exam_started_at', 'exam_finished_at',
        'answer_predict_opened_at', 'answer_official_opened_at',
    )
    list_per_page = 20


@admin.register(PrimePsatStudent)
class PrimePsatStudentAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'year', 'round', 'name', 'serial',
        'unit', 'department',
    )
    list_per_page = 20


@admin.register(PrimePsatRegisteredStudent)
class PrimePsatRegisteredStudentAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'user', 'student',
    )
    list_per_page = 20


@admin.register(PrimePsatAnswerCount)
class PrimePsatAnswerCountAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'year', 'round', 'subject', 'number',
    )
    list_per_page = 20
