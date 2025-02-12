from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models
from .models.choices import answer_choice


@admin.register(models.Leet)
class LeetAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'round', 'is_active']
    list_filter = ['year', 'exam', 'is_active']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'year', 'ex', 'subject', 'number', 'answer'
    ]
    list_filter = ['leet__year', 'leet__exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.leet.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.leet.exam}'


@admin.register(models.ResultStudent)
class ResultStudentAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'year', 'round',
        'name', 'serial', 'password',
    ]
    list_filter = [
        'leet__year',
        'leet__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.leet.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.leet.round}'


@admin.register(models.ResultRegistry)
class ResultRegistryAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'user_id', 'student_id',
        'year', 'round', 'name', 'serial', 'password',
    ]
    list_filter = [
        'student__leet__year',
        'student__leet__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='수험번호')
    def serial(self, obj):
        return f'{obj.student.serial}'

    @admin.display(description='비밀번호')
    def password(self, obj):
        return f'{obj.student.password}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.leet.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.leet.round}'


@admin.register(models.ResultAnswer)
class ResultAnswerAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'student_id', 'problem_id', 'year', 'round', 'name',
        'subject', 'number', 'answer', 'answer_correct',
    ]
    list_filter = [
        'student__leet__year',
        'student__leet__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.leet.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.leet.round}'

    @admin.display(description='과목')
    def subject(self, obj):
        return f'{obj.problem.subject}'

    @admin.display(description='번호')
    def number(self, obj):
        return f'{obj.problem.number}'

    @admin.display(description='정답')
    def answer_correct(self, obj):
        ans_correct = obj.problem.answer
        return answer_choice()[ans_correct]


@admin.register(models.ResultAnswerCount)
class ResultAnswerCountAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'problem_id',
        'year', 'round', 'subject', 'number', 'answer_correct',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_sum',
    ]
    list_filter = [
        'problem__leet__year',
        'problem__leet__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.problem.leet.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.problem.leet.round}'

    @admin.display(description='과목')
    def subject(self, obj):
        return f'{obj.problem.subject}'

    @admin.display(description='번호')
    def number(self, obj):
        return f'{obj.problem.number}'

    @admin.display(description='정답')
    def answer_correct(self, obj):
        ans_correct = obj.problem.answer
        return answer_choice()[ans_correct]


@admin.register(models.ResultScore)
class ResultScoreAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'student_id', 'year', 'round', 'name',
        'raw_subject_0', 'raw_subject_1', 'raw_sum',
        'subject_0', 'subject_1', 'sum',
    ]
    list_filter = [
        'student__leet__year',
        'student__leet__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.leet.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.leet.round}'


@admin.register(models.ResultRank)
class ResultRankAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'student_id', 'year', 'round', 'name',
        'subject_0', 'subject_1', 'sum', 'participants'
    ]
    list_filter = [
        'student__leet__year',
        'student__leet__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.leet.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.leet.round}'


@admin.register(models.ResultRankAspiration1)
class ResultRankAspiration1Admin(ModelAdmin):
    pass


@admin.register(models.ResultRankAspiration2)
class ResultRankAspiration2Admin(ModelAdmin):
    pass


@admin.register(models.ResultAnswerCountTopRank)
class ResultAnswerCountTopRankAdmin(ResultAnswerCountAdmin):
    pass


@admin.register(models.ResultAnswerCountMidRank)
class ResultAnswerCountMidRankAdmin(ResultAnswerCountAdmin):
    pass


@admin.register(models.ResultAnswerCountLowRank)
class ResultAnswerCountLowRankAdmin(ResultAnswerCountAdmin):
    pass
