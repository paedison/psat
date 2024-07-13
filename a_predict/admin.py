from django.contrib import admin

from .models import (
    PsatExam, PsatUnit, PsatDepartment,
    PsatStudent, PsatAnswerCount, PsatLocation,
)


@admin.register(PsatExam)
class PsatExamAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'exam',
        'page_opened_at', 'exam_started_at', 'exam_finished_at',
        'answer_predict_opened_at', 'answer_official_opened_at',
    )
    list_per_page = 20


@admin.register(PsatUnit)
class PsatUnitAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(PsatDepartment)
class PsatDepartmentAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(PsatStudent)
class PsatStudentAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(PsatAnswerCount)
class PsatAnswerCountAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(PsatLocation)
class PsatLocationAdmin(admin.ModelAdmin):
    list_per_page = 20
