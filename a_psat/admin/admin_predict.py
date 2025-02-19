from django.contrib import admin
from unfold.admin import ModelAdmin

from a_psat import models


@admin.register(models.PredictPsat)
class PredictPsatAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id',  'psat_info', 'is_active', 'page_opened_at', 'exam_started_at', 'exam_finished_at',
        'answer_predict_opened_at', 'answer_official_opened_at', 'predict_closed_at'
    ]
    list_filter = ['psat__year', 'psat__exam']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def psat_info(self, obj):
        return obj.psat_info


@admin.register(models.PredictCategory)
class PredictCategoryAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'exam', 'unit', 'department', 'order']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.PredictStatistics)
class PredictStatisticsAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'psat_info', 'department',
        'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average',
        'filtered_subject_0', 'filtered_subject_1', 'filtered_subject_2',
        'filtered_subject_3', 'filtered_average',
    ]
    list_filter = ['psat__year', 'psat__exam']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='출처')
    def psat_info(self, obj):
        return obj.psat_info


@admin.register(models.PredictStudent)
class PredictStudentAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'psat_info', 'user_id',
        'serial', 'name', 'password', 'unit', 'department', 'is_filtered',
    ]
    list_filter = [
        'psat__year',
        'psat__exam',
        'category__department',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def psat_info(self, obj):
        return obj.psat_info

    @admin.display(description='모집단위')
    def unit(self, obj):
        return obj.category.unit

    @admin.display(description='직렬')
    def department(self, obj):
        return obj.category.department


@admin.register(models.PredictAnswer)
class PredictAnswerAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'student_info', 'problem_info', 'answer', 'answer_official']
    list_filter = ['student']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='수험정보')
    def student_info(self, obj):
        return obj.student_info

    @admin.display(description='문제')
    def problem_info(self, obj):
        return obj.problem_info

    @admin.display(description='정답')
    def answer_official(self, obj):
        return obj.problem.get_answer_display()


@admin.register(models.PredictAnswerCount)
class PredictAnswerCountAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'problem_info', 'answer_official', 'answer_predict',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_sum',
    ]
    list_filter = ['problem__psat']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='문제')
    def problem_info(self, obj):
        return obj.problem_info

    @admin.display(description='정답')
    def answer_official(self, obj):
        return obj.problem.get_answer_display()


@admin.register(models.PredictScore)
class PredictScoreAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'psat_info', 'student_id', 'name', 'department',
        'subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'average'
    ]
    list_filter = ['student__psat']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def psat_info(self, obj):
        return obj.psat_info

    @admin.display(description='이름')
    def name(self, obj):
        return obj.student.name

    @admin.display(description='직렬')
    def department(self, obj):
        return obj.student.category.department


@admin.register(models.PredictRankTotal)
class PredictRankTotalAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'psat_info', 'student_id', 'name', 'department',
        'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average', 'participants'
    ]
    list_filter = ['student__psat']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def psat_info(self, obj):
        return obj.psat_info

    @admin.display(description='이름')
    def name(self, obj):
        return obj.student.name

    @admin.display(description='직렬')
    def department(self, obj):
        return obj.student.category.department


@admin.register(models.PredictRankCategory)
class PredictRankCategoryAdmin(ModelAdmin):
    pass


@admin.register(models.PredictAnswerCountTopRank)
class PredictAnswerCountTopRankAdmin(PredictAnswerCountAdmin):
    pass


@admin.register(models.PredictAnswerCountMidRank)
class PredictAnswerCountMidRankAdmin(PredictAnswerCountAdmin):
    pass


@admin.register(models.PredictAnswerCountLowRank)
class PredictAnswerCountLowRankAdmin(PredictAnswerCountAdmin):
    pass


@admin.register(models.PredictLocation)
class PredictLocationAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'psat_info', 'department', 'serial_start', 'serial_end',
        'region', 'school', 'address', 'contact',
    ]
    list_filter = ['psat']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def psat_info(self, obj):
        return obj.psat_info

    @admin.display(description='직렬')
    def department(self, obj):
        return obj.category.department
