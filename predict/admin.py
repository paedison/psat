from django.contrib import admin

from .models import (
    Exam, Student, Answer, AnswerCount, Statistics, StatisticsVirtual,
)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'category', 'year', 'ex', 'round',
        'predict_open_datetime', 'start_datetime', 'end_datetime', 'answer_open_datetime',
    )
    list_per_page = 20


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(AnswerCount)
class AnswerCountAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(StatisticsVirtual)
class StatisticsVirtualAdmin(admin.ModelAdmin):
    list_per_page = 20
