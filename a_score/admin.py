from django.contrib import admin

from . import models


@admin.register(models.PrimePsatExam)
class PrimePsatExamAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id',
        'page_opened_at', 'exam_started_at', 'exam_finished_at',
        'answer_predict_opened_at', 'answer_official_opened_at',
    )
    list_per_page = 20


@admin.register(models.PrimePsatStudent)
class PrimePsatStudentAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'year', 'round', 'name', 'serial',
        'unit', 'department',
    )
    list_per_page = 20


@admin.register(models.PrimePsatRegisteredStudent)
class PrimePsatRegisteredStudentAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'user', 'student',
    )
    list_per_page = 20


@admin.register(models.PrimePsatAnswerCount)
class PrimePsatAnswerCountAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'year', 'round', 'subject', 'number',
    )
    list_per_page = 20


@admin.register(models.PrimePoliceExam)
class PrimePsatExamAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id',
        'page_opened_at', 'exam_started_at', 'exam_finished_at',
        'answer_predict_opened_at', 'answer_official_opened_at',
    )
    list_per_page = 20


@admin.register(models.PrimePoliceStudent)
class PrimePsatStudentAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'year', 'round', 'name', 'serial',
        'unit', 'department',
    )
    list_per_page = 20


@admin.register(models.PrimePoliceRegisteredStudent)
class PrimePsatRegisteredStudentAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'user', 'student',
    )
    list_per_page = 20


@admin.register(models.PrimePoliceAnswerCount)
class PrimePsatAnswerCountAdmin(admin.ModelAdmin):
    list_display = list_display_links = (
        'id', 'year', 'round', 'subject', 'number',
    )
    list_per_page = 20
