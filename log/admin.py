from django.contrib import admin

from log.models import AccountLog, RequestLog, ProblemLog, LikeLog, RateLog, AnswerLog


class GeneralLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'session_key', 'log_url', 'log_content')
    list_per_page = 20


class ProblemLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'session_key', 'problem')
    list_per_page = 20


class LikeLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'problem', 'is_liked')
    list_per_page = 20


class RateLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'problem', 'difficulty_rated')
    list_per_page = 20


class AnswerLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'problem', 'submitted_answer', 'is_correct')
    list_per_page = 20


admin.site.register(AccountLog, GeneralLogAdmin)
admin.site.register(RequestLog, GeneralLogAdmin)
admin.site.register(ProblemLog, ProblemLogAdmin)
admin.site.register(LikeLog, LikeLogAdmin)
admin.site.register(RateLog, RateLogAdmin)
admin.site.register(AnswerLog, AnswerLogAdmin)
