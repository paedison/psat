from django.contrib import admin

from .models import AccountLog, RequestLog, ProblemLog, LikeLog, RateLog, AnswerLog


class GeneralLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'session_key', 'log_url', 'log_content')
    list_per_page = 20


class ProblemLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'evaluation', 'user_id', 'session_key', 'problem_id')
    list_per_page = 20


class LikeLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'evaluation', 'user_id', 'problem_id', 'is_liked')
    list_per_page = 20


class RateLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'evaluation', 'user_id', 'problem_id', 'difficulty_rated')
    list_per_page = 20


class AnswerLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'evaluation', 'user_id', 'problem_id', 'submitted_answer', 'is_correct')
    list_per_page = 20


admin.site.register(AccountLog, GeneralLogAdmin)
admin.site.register(RequestLog, GeneralLogAdmin)
admin.site.register(ProblemLog, ProblemLogAdmin)
admin.site.register(LikeLog, LikeLogAdmin)
admin.site.register(RateLog, RateLogAdmin)
admin.site.register(AnswerLog, AnswerLogAdmin)
