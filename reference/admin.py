from django.contrib import admin

from .models import Category, Exam, Subject, Psat, PsatProblem


admin.site.register(Category)
admin.site.register(Exam)
admin.site.register(Subject)
admin.site.register(Psat)
admin.site.register(PsatProblem)
