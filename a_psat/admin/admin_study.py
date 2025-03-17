from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from a_psat import models


@admin.register(models.StudyCategory)
class StudyCategoryAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'season', 'study_type', 'name']
    list_filter = ['season', 'study_type', 'name']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.StudyPsat)
class StudyPsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id','category_info', 'round']
    list_filter = ['category__season', 'category__study_type']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category')

    @admin.display(description='카테고리')
    def category_info(self, obj):
        return obj.category_info


@admin.register(models.StudyProblem)
class StudyProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'psat_info', 'number', 'answer',  'reference']
    list_filter = ['psat__category__season', 'psat__category__study_type']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'psat', 'psat__category', 'problem', 'problem__psat',
        )

    @admin.display(description='회차 정보')
    def psat_info(self, obj):
        return obj.psat_info

    @admin.display(description='정답')
    def answer(self, obj):
        return obj.problem.get_answer_display()

    @admin.display(description='출처')
    def reference(self, obj):
        return obj.problem_reference


@admin.register(models.StudyOrganization)
class StudyOrganizationAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'name', 'logo_image']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True

    @admin.display(description='로고')
    def logo_image(self, obj):
        if obj.logo:
            return format_html('<img src="{}" height="50" width="50" style="border-radius:5px;" />', obj.logo.url)
        return 'No Image'


@admin.register(models.StudyCurriculum)
class StudyCurriculumAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'name', 'semester', 'category_info']
    list_filter = ['year', 'organization__name']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'category')

    @admin.display(description='교육기관명')
    def name(self, obj):
        return obj.organization.name

    @admin.display(description='카테고리')
    def category_info(self, obj):
        return obj.category_info


@admin.register(models.StudyCurriculumSchedule)
class StudyCurriculumScheduleAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'curriculum', 'lecture_number', 'lecture_theme', 'lecture_round', 'homework_round',
        'lecture_open_datetime', 'homework_end_datetime', 'lecture_datetime',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.StudyStudent)
class StudyStudentAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'updated_at', 'curriculum', 'serial', 'name', 'user']
    list_filter = ['curriculum']
    list_select_related = ['curriculum', 'curriculum__organization', 'curriculum__category']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('curriculum', 'curriculum__organization', 'curriculum__category')


@admin.register(models.StudyAnswer)
class StudyAnswerAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'student_info',
        'problem', 'answer', 'answer_official', 'problem_reference'
    ]
    list_filter = ['student']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student', 'student__curriculum', 'student__curriculum__organization',
            'problem', 'problem__psat', 'problem__problem', 'problem__problem__psat',
        )

    @admin.display(description='수험정보')
    def student_info(self, obj):
        return f'{obj.student_info}({obj.curriculum_info})'

    @admin.display(description='정답')
    def answer_official(self, obj):
        return obj.problem.problem.get_answer_display()

    @admin.display(description='출처')
    def problem_reference(self, obj):
        return obj.problem_reference


@admin.register(models.StudyAnswerCount)
class StudyAnswerCountAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'problem_info', 'answer_official', 'problem_reference',
        'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
        'count_0', 'count_multiple', 'count_sum',
    ]
    list_filter = ['problem__psat']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'problem', 'problem__psat', 'problem__problem', 'problem__problem__psat',
            'problem__psat__category'
        )

    @admin.display(description='문제')
    def problem_info(self, obj):
        return obj.problem_info

    @admin.display(description='출처')
    def problem_reference(self, obj):
        return obj.problem_reference

    @admin.display(description='정답')
    def answer_official(self, obj):
        return obj.problem.problem.get_answer_display()


@admin.register(models.StudyResult)
class StudyResultAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'curriculum_info', 'student_info', 'psat_info', 'score', 'rank']
    list_filter = ['student']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student', 'student__curriculum', 'psat', 'psat__category',
            'student__curriculum__organization',
        )

    @admin.display(description='커리큘럼')
    def curriculum_info(self, obj):
        return obj.curriculum_info

    @admin.display(description='수험정보')
    def student_info(self, obj):
        return obj.student_info

    @admin.display(description='수험정보')
    def psat_info(self, obj):
        return obj.psat.psat_info


@admin.register(models.StudyAnswerCountTopRank)
class StudyAnswerCountTopRankAdmin(StudyAnswerCountAdmin):
    pass


@admin.register(models.StudyAnswerCountMidRank)
class StudyAnswerCountMidRankAdmin(StudyAnswerCountAdmin):
    pass


@admin.register(models.StudyAnswerCountLowRank)
class StudyAnswerCountLowRankAdmin(StudyAnswerCountAdmin):
    pass
