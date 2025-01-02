from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models
from .models.choices import answer_choice


@admin.register(models.Psat)
class PsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'round', 'is_active']
    list_filter = ['year', 'exam', 'is_active']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Category)
class CategoryAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'exam', 'unit', 'department', 'order']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'year', 'ex', 'subject', 'number', 'answer'
    ]
    list_filter = ['psat__year', 'psat__exam', 'subject']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.psat.exam}'


@admin.register(models.ResultStatistics)
class ResultStatisticsAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'psat', 'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average'
    ]
    list_filter = ['psat__year', 'psat__exam']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.psat.exam}'


@admin.register(models.ResultStudent)
class ResultStudentAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'year', 'round',
        'name', 'serial', 'password', 'unit', 'department',
    ]
    list_filter = [
        'psat__year',
        'psat__round',
        'category__department',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.psat.round}'

    @admin.display(description='모집단위')
    def unit(self, obj):
        return f'{obj.category.unit}'

    @admin.display(description='직렬')
    def department(self, obj):
        return f'{obj.category.department}'


@admin.register(models.ResultRegistry)
class ResultRegistryAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'user_id', 'student_id',
        'year', 'round', 'name', 'serial', 'password', 'department',
    ]
    list_filter = [
        'student__psat__year',
        'student__psat__round',
        'student__category__department',
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
        return f'{obj.student.psat.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.psat.round}'

    @admin.display(description='직렬')
    def department(self, obj):
        return f'{obj.student.category.department}'


@admin.register(models.ResultAnswer)
class ResultAnswerAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'student_id', 'problem_id', 'year', 'round', 'name', 'department',
        'subject', 'number', 'answer', 'answer_correct',
    ]
    list_filter = [
        'student__psat__year',
        'student__psat__round',
        'student__category__department',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='직렬')
    def department(self, obj):
        return f'{obj.student.category.department}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.psat.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.psat.round}'

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
        'problem__psat__year',
        'problem__psat__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.problem.psat.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.problem.psat.round}'

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
        'id', 'student_id', 'year', 'round', 'name', 'department',
        'subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'average'
    ]
    list_filter = [
        'student__psat__year',
        'student__psat__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='직렬')
    def department(self, obj):
        return f'{obj.student.category.department}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.psat.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.psat.round}'

    @admin.display(description='PSAT 평균')
    def average(self, obj):
        return f'{obj.average}'


@admin.register(models.ResultRankTotal)
class ResultRankTotalAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'student_id', 'year', 'round', 'name', 'department',
        'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average', 'participants'
    ]
    list_filter = [
        'student__psat__year',
        'student__psat__round',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='이름')
    def name(self, obj):
        return f'{obj.student.name}'

    @admin.display(description='직렬')
    def department(self, obj):
        return f'{obj.student.category.department}'

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.student.psat.year}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.student.psat.round}'


@admin.register(models.ResultRankCategory)
class ResultRankCategoryAdmin(ResultRankTotalAdmin):
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


@admin.register(models.PredictStudent)
class PredictStudentAdmin(ResultStudentAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'year', 'round', 'user_id',
        'name', 'serial', 'password', 'unit', 'department', 'is_filtered',
    ]


@admin.register(models.PredictAnswer)
class PredictAnswerAdmin(ResultAnswerAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'student_id', 'problem_id', 'year', 'round', 'name', 'department',
        'subject', 'number', 'answer', 'answer_correct',
    ]


@admin.register(models.PredictAnswerCount)
class PredictAnswerCountAdmin(ResultAnswerCountAdmin):
    pass


@admin.register(models.PredictScore)
class PredictScoreAdmin(ResultScoreAdmin):
    pass


@admin.register(models.PredictRankTotal)
class PredictRankTotalAdmin(ResultRankTotalAdmin):
    pass


@admin.register(models.PredictRankCategory)
class PredictRankCategoryAdmin(ResultRankTotalAdmin):
    pass


@admin.register(models.PredictAnswerCountTopRank)
class PredictAnswerCountTopRankAdmin(ResultAnswerCountAdmin):
    pass


@admin.register(models.PredictAnswerCountMidRank)
class PredictAnswerCountMidRankAdmin(ResultAnswerCountAdmin):
    pass


@admin.register(models.PredictAnswerCountLowRank)
class PredictAnswerCountLowRankAdmin(ResultAnswerCountAdmin):
    pass
