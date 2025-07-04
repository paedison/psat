from django.contrib import admin
from unfold.admin import ModelAdmin

from a_leet import models

SCORE_FIELDS = [
    'raw_subject_0', 'raw_subject_1', 'raw_sum',
    'subject_0', 'subject_1', 'sum',
]
FILTERED_SCORE_FIELDS = [f'filtered_{fld}' for fld in SCORE_FIELDS]


@admin.register(models.PredictLeet)
class PredictLeetAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id',  'leet_info', 'is_active', 'page_opened_at', 'exam_started_at', 'exam_finished_at',
        'answer_predict_opened_at', 'answer_official_opened_at', 'predict_closed_at'
    ]
    list_filter = ['leet__year']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def leet_info(self, obj):
        return obj.leet_info


@admin.register(models.PredictStatistics)
class PredictStatisticsAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'leet_info', 'aspiration'] + SCORE_FIELDS + FILTERED_SCORE_FIELDS
    list_filter = ['leet__year']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='출처')
    def leet_info(self, obj):
        return obj.leet_info


@admin.register(models.PredictStudent)
class PredictStudentAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'leet_info', 'user_id',
        'serial', 'name', 'password', 'aspiration_1', 'aspiration_2', 'is_filtered',
    ]
    list_filter = ['leet__year', 'aspiration_1', 'aspiration_2']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def leet_info(self, obj):
        return obj.leet_info


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
    list_filter = ['problem__leet']
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
        'id', 'leet_info', 'student_id', 'name', 'aspiration_1', 'aspiration_2',
    ] + SCORE_FIELDS
    list_filter = ['student__leet']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def leet_info(self, obj):
        return obj.leet_info

    @admin.display(description='이름')
    def name(self, obj):
        return obj.student.name

    @admin.display(description='1지망')
    def aspiration_1(self, obj):
        return obj.student.aspiration_1

    @admin.display(description='2지망')
    def aspiration_2(self, obj):
        return obj.student.aspiration_2


@admin.register(models.PredictRank)
class PredictRankAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'leet_info', 'student_id', 'name', 'aspiration_1', 'aspiration_2',
        'subject_0', 'subject_1', 'sum', 'participants'
    ]
    list_filter = ['student__leet']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='출처')
    def leet_info(self, obj):
        return obj.leet_info

    @admin.display(description='이름')
    def name(self, obj):
        return obj.student.name

    @admin.display(description='1지망')
    def aspiration_1(self, obj):
        return obj.student.aspiration_1

    @admin.display(description='2지망')
    def aspiration_2(self, obj):
        return obj.student.aspiration_2


@admin.register(models.PredictRankAspiration1)
class PredictRankAspiration1Admin(PredictRankAdmin):
    pass


@admin.register(models.PredictRankAspiration2)
class PredictRankAspiration2Admin(PredictRankAdmin):
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
