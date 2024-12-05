import dataclasses

from django.urls import reverse

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest
from .. import forms
from .. import models


@dataclasses.dataclass
class ScoreExamVars:
    psat: models.Psat

    # Template variables
    data_answer_predict: list[list[dict]] = dataclasses.field(default_factory=list)
    answer_confirmed: list[bool] = dataclasses.field(default_factory=list)
    data_answer_official_tuple: tuple[list[list[dict]], bool] = dataclasses.field(default_factory=tuple)
    data_answer_student: list[list[dict]] = dataclasses.field(default_factory=list)
    info_answer_student: list = dataclasses.field(default_factory=list)
    stat: dict[str, list[dict]] = dataclasses.field(default_factory=dict)

    # Template constants
    info = {'menu': 'predict', 'view_type': 'predict'}
    icon_menu = icon_set_new.ICON_MENU['score']
    score_template_table_1 = 'a_prime/snippets/detail_sheet_score_table_1.html'
    score_template_table_2 = 'a_prime/snippets/detail_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    @property
    def exam_year(self):
        return self.psat.year

    @property
    def exam_round(self):
        return self.psat.round

    @property
    def exam_info(self):
        return {'psat__year': self.exam_year, 'psat__round': self.exam_round}

    def get_problem_info(self, field: str, number: int):
        return {
            'year': self.exam_year, 'round': self.exam_round,
            'subject': field, 'number': number,
        }

    @property
    def exam_url_kwargs(self):
        return {'exam_year': self.exam_year, 'exam_round': self.exam_round}

    @property
    def url_list(self):
        return reverse('prime:score-list')

    @property
    def url_modal(self):
        return reverse('prime:score-modal', args=[self.exam_url_kwargs])

    @property
    def url_detail(self):
        return reverse('prime:score-detail', kwargs=self.exam_url_kwargs)

    @property
    def url_student_register(self):
        return reverse('score:prime-student-register', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_list(self):
        return reverse('score:prime-admin-list')

    @property
    def url_admin_detail(self):
        return reverse('predict:admin-detail', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_update(self):
        return reverse('predict:admin-update', kwargs=self.exam_url_kwargs)

    @property
    def student_exam_info(self):
        return {
            'student__year': self.exam_year, 'student__round': self.exam_round
        }


@dataclasses.dataclass
class ScorePsatExamVars(ScoreExamVars):
    exam_model = models.Psat
    student_model = models.ResultStudent
    answer_model = models.ResultAnswer
    answer_count_model = models.ResultAnswerCount
    score_model = models.ResultScore
    rank_total_model = models.ResultRankTotal
    rank_category_model = models.ResultRankCategory
    student_form = forms.PrimePsatStudentForm

    # Answer count fields constant
    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5']
    all_count_fields = count_fields + ['count_multiple', 'count_total']

    def get_count_default(self):
        return {fld: 0 for fld in self.all_count_fields}

    # Sum or average fields
    avg_field = 'psat_avg'
    sum_fields = ['eoneo', 'jaryo', 'sanghwang']

    sub_list = ['헌법', '언어', '자료', '상황']
    subject_list = ['헌법', '언어논리', '자료해석', '상황판단']
    admin_subject_list = ['PSAT', '헌법', '언어논리', '자료해석', '상황판단']
    subject_vars = {
        '헌법': ('헌법', 'heonbeob'), '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
    }
    subject_fields = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
    score_fields = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
    admin_score_fields = ['psat_avg', 'heonbeob', 'eoneo', 'jaryo', 'sanghwang']
    field_vars = {
        'heonbeob': ('헌법', '헌법'), 'eoneo': ('언어', '언어논리'), 'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'), 'psat_avg': ('평균', 'PSAT 평균'),
    }
    problem_count = {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}

    @property
    def exam(self):
        return self.exam_model.objects.filter(year=self.exam_year, round=self.exam_round).first()

    def get_student(self, request: HtmxHttpRequest):
        if request.user.is_authenticated:
            return self.student_model.objects.filter(
                **self.exam_info, registries__user=request.user).first()

    @property
    def qs_answer_count(self):
        return self.answer_count_model.objects.filter(**self.exam_info).order_by('subject', 'number')

    @property
    def sub_title(self):
        return f'제{self.exam_round}회 프라임모의고사 성적표'

    def get_subject_field(self, subject):
        for field, subject_tuple in self.field_vars.items():
            if field == subject:
                return field
            if subject_tuple[0] == subject:
                return field
            if subject_tuple[1] == subject:
                return field

    @property
    def icon_subject(self):
        return [icon_set_new.ICON_SUBJECT[sub] for sub in self.sub_list]

    @property
    def info_tab(self):
        return {
            'id': ''.join([str(i) for i in range(len(self.subject_vars))]),
        }

    @property
    def answer_tab(self):
        return {
            'id': ''.join([str(i) for i in range(len(self.sub_list))]),
            'title': self.sub_list,
        }

    def get_empty_data_answer(self):
        return [
            [
                {'no': no, 'ans': 0, 'field': fld} for no in range(1, self.problem_count[fld] + 1)
            ] for fld in self.subject_fields
        ]

    def get_field_idx(self, field):
        return self.subject_fields.index(field)
