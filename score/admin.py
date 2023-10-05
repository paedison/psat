from django.contrib import admin

from .models import (
    Unit, Department, Student,
    TemporaryAnswer, ConfirmedAnswer, DummyAnswer,
    AnswerCount,
)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(TemporaryAnswer)
class TemporaryAnswerAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(ConfirmedAnswer)
class ConfirmedAnswerAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(DummyAnswer)
class DummyAnswerAdmin(admin.ModelAdmin):
    list_per_page = 20


@admin.register(AnswerCount)
class AnswerCountAdmin(admin.ModelAdmin):
    list_per_page = 20
