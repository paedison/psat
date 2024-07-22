import dataclasses

from django.urls import reverse

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest
from .. import forms
from ..models import prime_psat_models, prime_police_models


@dataclasses.dataclass
class ScoreExamVars:
    exam_type: str
    exam_year: int
    exam_round: int

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
    score_template_table_1 = 'a_score/snippets/detail_sheet_score_table_1.html'
    score_template_table_2 = 'a_score/snippets/detail_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'round': self.exam_round}

    def get_problem_info(self, field: str, number: int):
        return {
            'year': self.exam_year, 'round': self.exam_round,
            'subject': field, 'number': number,
        }

    @property
    def exam_url_kwargs(self):
        return {'exam_type': self.exam_type, 'exam_year': self.exam_year, 'exam_round': self.exam_round}

    @property
    def url_list(self):
        return reverse('score:prime-list', args=[self.exam_type])

    @property
    def url_modal(self):
        return reverse('score:prime-modal', args=[self.exam_url_kwargs])

    @property
    def url_detail(self):
        return reverse('score:prime-detail', kwargs=self.exam_url_kwargs)

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
class ScorePrimePsatExamVars(ScoreExamVars):
    exam_model = prime_psat_models.PrimePsatExam
    student_model = prime_psat_models.PrimePsatStudent
    answer_count_model = prime_psat_models.PrimePsatAnswerCount
    registered_student_model = prime_psat_models.PrimePsatRegisteredStudent
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
                **self.exam_info, registered_students__user=request.user).first()

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


@dataclasses.dataclass
class ScorePrimePoliceExamVars(ScoreExamVars):
    selection: str = 'minbeob'

    exam_model = prime_police_models.PrimePoliceExam
    student_model = prime_police_models.PrimePoliceStudent
    answer_count_model = prime_police_models.PrimePoliceAnswerCount
    student_form = forms.PrimePoliceStudentForm

    # Answer count fields constant
    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    all_count_fields = count_fields + ['count_multiple', 'count_total']

    def get_count_default(self):
        return {fld: 0 for fld in self.all_count_fields}

    # Sum fields
    avg_field = 'sum'

    @property
    def sum_fields(self):
        return ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', self.selection]

    @property
    def sub_title(self):
        return f'제{self.exam_round}회 프라임모의고사 성적표'

    @property
    def sub_list(self):
        sub_dict = {'haengbeob': '행법', 'haenghag': '행학', 'minbeob': '민법'}
        return ['형사', '헌법', '경찰', '범죄', sub_dict[self.selection]]

    @property
    def subject_list(self):
        subject_dict = {'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙'}
        return ['형사학', '헌법', '경찰학', '범죄학', subject_dict[self.selection]]

    @property
    def subject_vars(self):
        subject_vars_dict = {
            'haengbeob': ('행법', ('행정법', 'haengbeob')),
            'haenghag': ('행학', ('행정학', 'haenghag')),
            'minbeob': ('민법', ('민법총칙', 'minbeob')),
        }
        return {
            '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
            '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
            subject_vars_dict[self.selection][0]: subject_vars_dict[self.selection][1],
            '총점': ('총점', 'sum')
        }

    @property
    def subject_fields(self):
        return ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', self.selection]

    @property
    def score_fields(self):
        return ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', self.selection, 'sum']

    @property
    def field_vars(self):
        field_vars_dict = {
            'haengbeob': ('행법', '행정법'), 'haenghag': ('행학', '행정학'), 'minbeob': ('민법', '민법총칙'),
        }
        return {
            'hyeongsa': ('형사', '형사학'), 'heonbeob': ('헌법', '헌법'),
            'gyeongchal': ('경찰', '경찰학'), 'beomjoe': ('범죄', '범죄학'),
            self.selection: field_vars_dict[self.selection], 'sum': ('총점', '총점'),
        }

    @property
    def selection_choice(self):
        return [
            {'field': 'minbeob', 'name': '민법총칙'},
            {'field': 'haenghag', 'name': '행정학'},
            {'field': 'haengbeob', 'name': '행정법'},
        ]

    @property
    def problem_count(self):
        return {fld: 40 for fld in self.subject_fields}

    @property
    def icon_subject(self):
        return ['' for _ in self.sub_list]

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
            'prefix_submit': [f'{field}_submit' for field in self.subject_fields],
            'prefix_predict': [f'{field}_predict' for field in self.subject_fields],
        }

    def get_empty_data_answer(self):
        return [
            [
                {'no': no, 'ans': 0, 'field': fld} for no in range(1, self.problem_count[fld] + 1)
            ] for fld in self.subject_fields
        ]

    def get_field_idx(self, field):
        return self.subject_fields.index(field)


@dataclasses.dataclass
class ScorePrimePoliceAdminExamVars(ScorePrimePoliceExamVars):

    @property
    def sum_fields(self):
        return self.subject_fields

    @property
    def sub_list(self):
        return ['형사', '헌법', '경찰', '범죄', '민법', '행학', '행법']

    @property
    def subject_list(self):
        return ['형사학', '헌법', '경찰학', '범죄학', '민법총칙', '행정학', '행정법']

    @property
    def admin_subject_list(self):
        return ['총점', '형사학', '헌법', '경찰학', '범죄학', '민법총칙', '행정학', '행정법']

    @property
    def subject_vars(self):
        return {
            '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
            '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
            '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
            '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
        }

    @property
    def subject_fields(self):
        return [
            'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob',
        ]

    @property
    def score_fields(self):
        return [
            'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob', 'sum',
        ]

    @property
    def admin_score_fields(self):
        return [
            'sum', 'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe',
            'minbeob', 'haenghag', 'haengbeob',
        ]

    @property
    def field_vars(self):
        return {
            'hyeongsa': ('형사', '형사학'), 'heonbeob': ('헌법', '헌법'),
            'gyeongchal': ('경찰', '경찰학'), 'beomjoe': ('범죄', '범죄학'),
            'minbeob': ('민법', '민법총칙'), 'haenghag': ('행학', '행정학'),
            'haengbeob': ('행법', '행정법'), 'sum': ('총점', '총점'),
        }
