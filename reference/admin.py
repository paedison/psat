from django.contrib import admin

from .models.base_models import Category, Exam, Subject
from .models.psat_models import Psat, PsatProblem
from .models.prime_models import Prime, PrimeProblem


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ['id', 'name']


class ExamAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'abbr', 'label', 'name', 'remark']
    list_display_links = ['id', 'category', 'abbr', 'label', 'name', 'remark']


class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'abbr', 'name']
    list_display_links = ['id', 'category', 'abbr', 'name']


class PsatAdmin(admin.ModelAdmin):
    list_display = ['id', 'year', 'exam', 'subject']
    list_display_links = ['id', 'year', 'exam', 'subject']


class PsatProblemAdmin(admin.ModelAdmin):
    list_display = ['id', 'psat', 'number', 'answer', 'question']
    list_display_links = ['id', 'psat', 'number', 'answer', 'question']


class PrimeAdmin(admin.ModelAdmin):
    list_display = ['id', 'year', 'round', 'exam', 'subject']
    list_display_links = ['id', 'year', 'round', 'exam', 'subject']


class PrimeProblemAdmin(admin.ModelAdmin):
    list_display = ['id', 'prime', 'number', 'answer']
    list_display_links = ['id', 'prime', 'number', 'answer']


admin.site.register(Category, CategoryAdmin)
admin.site.register(Exam, ExamAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Psat, PsatAdmin)
admin.site.register(PsatProblem, PsatProblemAdmin)
admin.site.register(Prime, PrimeAdmin)
admin.site.register(PrimeProblem, PrimeProblemAdmin)
