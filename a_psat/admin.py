from django.contrib import admin
from unfold.admin import ModelAdmin

from . import models


@admin.register(models.Psat)
class PsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'exam', 'order', 'is_active']
    list_filter = ['year', 'exam', 'is_active']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.Problem)
class ProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'ex', 'sub', 'num', 'answer', 'question']
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

    @admin.display(description='과목')
    def sub(self, obj):
        return f'{obj.subject}'

    @admin.display(description='번호')
    def num(self, obj):
        return f'{obj.number}'


@admin.register(models.ProblemOpen)
class ProblemOpenAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user_id', 'reference', 'ip_address']
    fields = ['user_id', 'reference', 'ip_address']


@admin.register(models.ProblemLike)
class ProblemLikeAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'is_liked']
    fields = ['user', 'problem', 'is_liked']


@admin.register(models.ProblemRate)
class ProblemRateAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'rating']
    fields = ['user', 'problem', 'rating']


@admin.register(models.ProblemSolve)
class ProblemSolveAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'answer', 'is_correct']
    fields = ['user', 'problem', 'answer', 'is_correct']


@admin.register(models.ProblemMemo)
class ProblemMemoAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'content']
    fields = ['user', 'problem', 'content']


@admin.register(models.ProblemTag)
class ProblemTagAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'name', 'slug']
    fields = ['tag', 'slug']


@admin.register(models.ProblemTaggedItem)
class ProblemTaggedItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'reference', 'tag_name']
    fields = ['user', 'content_object', 'tag', 'active']


@admin.register(models.ProblemCollection)
class ProblemCollectionAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'user', 'title', 'order']
    fields = ['user', 'title', 'order']


@admin.register(models.ProblemCollectionItem)
class ProblemCollectionItemAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'created_at', 'reference', 'collect_title', 'order']
    fields = ['collect', 'problem', 'order']


@admin.register(models.Lecture)
class LectureAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'subject', 'title', 'sub_title', 'youtube_id', 'order', 'created_at']
    list_filter = ['subject', 'title', 'sub_title', 'youtube_id', 'order']


@admin.register(models.LectureOpen)
class LectureOpenAdmin(ModelAdmin):
    pass


@admin.register(models.LectureLike)
class LectureLikeAdmin(ModelAdmin):
    pass


@admin.register(models.LectureMemo)
class LectureMemoAdmin(ModelAdmin):
    pass


@admin.register(models.LectureTag)
class LectureTagAdmin(ModelAdmin):
    pass


@admin.register(models.LectureTaggedItem)
class LectureTaggedItemAdmin(ModelAdmin):
    pass


@admin.register(models.PredictPsat)
class PredictPsatAdmin(ModelAdmin):
    list_display = list_display_links = ['id', 'year', 'ex', 'is_active']
    list_filter = ['psat__year', 'psat__exam']
    ordering = ['-id']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.psat.exam}'


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
        'id', 'psat', 'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average'
    ]
    list_filter = ['psat__year', 'psat__exam']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    search_fields = ['data']
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.psat.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.psat.psat.exam}'


@admin.register(models.PredictStudent)
class PredictStudentAdmin(ModelAdmin):
    list_display = list_display_links = [
        'id', 'created_at', 'year', 'ex', 'user_id',
        'name', 'serial', 'password', 'unit', 'department', 'is_filtered',
    ]
    list_filter = [
        'psat__year',
        'psat__exam',
        # 'psat__psat__year',
        # 'psat__psat__exam',
        'category__department',
    ]
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='연도')
    def year(self, obj):
        return f'{obj.psat.year}'

    @admin.display(description='시험')
    def ex(self, obj):
        return f'{obj.psat.psat.exam}'

    @admin.display(description='모집단위')
    def unit(self, obj):
        return f'{obj.category.unit}'

    @admin.display(description='직렬')
    def department(self, obj):
        return f'{obj.category.department}'


@admin.register(models.StudyCategory)
class StudyCategoryAdmin(ModelAdmin):
    list_display = list_display_links = ['season', 'study_type', 'name']
    list_filter = ['season', 'study_type', 'name']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True


@admin.register(models.StudyPsat)
class StudyPsatAdmin(ModelAdmin):
    list_display = list_display_links = ['season', 'study_type', 'round']
    list_filter = ['category__season', 'category__study_type']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='시즌')
    def season(self, obj):
        return f'{obj.category.season}'

    @admin.display(description='종류')
    def study_type(self, obj):
        return f'{obj.category.study_type}'


@admin.register(models.StudyProblem)
class StudyProblemAdmin(ModelAdmin):
    list_display = list_display_links = ['season', 'study_type', 'round', 'number', 'reference']
    list_filter = ['psat__category__season', 'psat__category__study_type']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='시즌')
    def season(self, obj):
        return f'{obj.psat.category.season}'

    @admin.display(description='종류')
    def study_type(self, obj):
        return f'{obj.psat.category.study_type}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.psat.round}'

    @admin.display(description='출처')
    def reference(self, obj):
        return f'{obj.problem.reference}'


@admin.register(models.StudyStatistics)
class StudyStatisticsAdmin(ModelAdmin):
    list_display = list_display_links = ['season', 'study_type', 'round']
    list_filter = ['psat__category__season', 'psat__category__study_type']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='시즌')
    def season(self, obj):
        return f'{obj.psat.category.season}'

    @admin.display(description='종류')
    def study_type(self, obj):
        return f'{obj.psat.category.study_type}'

    @admin.display(description='회차')
    def round(self, obj):
        return f'{obj.psat.round}'


@admin.register(models.StudyOrganization)
class StudyOrganizationAdmin(ModelAdmin):
    list_display = list_display_links = ['name', 'logo']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True


@admin.register(models.StudyCurriculum)
class StudyCurriculumAdmin(ModelAdmin):
    list_display = list_display_links = ['year', 'name', 'semester', 'season', 'study_type']
    list_filter = ['year', 'organization__name']
    show_facets = admin.ShowFacets.ALWAYS
    save_on_top = True
    show_full_result_count = True

    @admin.display(description='교육기관명')
    def name(self, obj):
        return f'{obj.organization.name}'

    @admin.display(description='시즌')
    def season(self, obj):
        return f'{obj.category.season}'

    @admin.display(description='종류')
    def study_type(self, obj):
        return f'{obj.category.study_type}'
