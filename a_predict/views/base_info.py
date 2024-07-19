import dataclasses

from django.urls import reverse

from common.constants import icon_set_new
from .. import forms
from ..models import psat_models, police_models


@dataclasses.dataclass
class ExamVars:
    exam_year: int
    exam_exam: str
    exam_round: int

    info = {'menu': 'predict', 'view_type': 'predict'}
    score_template_table_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
    score_template_table_2 = 'a_predict/snippets/index_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'prefix_all': ['my_all', 'total_all', 'department_all'],
        'prefix_filtered': ['my_filtered', 'total_filtered', 'department_filtered'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'exam': self.exam_exam, 'round': self.exam_round}

    @property
    def exam_url_kwargs(self):
        return {'exam_year': self.exam_year, 'exam_exam': self.exam_exam, 'exam_round': self.exam_round}

    @property
    def url_index(self):
        return reverse('predict:index')

    @property
    def url_detail(self):
        return reverse('predict:psat-detail', kwargs=self.exam_url_kwargs)

    @property
    def student_exam_info(self):
        return {
            'student__year': self.exam_year, 'student__exam': self.exam_exam, 'student__round': self.exam_round
        }


@dataclasses.dataclass
class PsatExamVars(ExamVars):
    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5']
    avg_field = 'psat_avg'
    sum_fields = ['eoneo', 'jaryo', 'sanghwang']

    exam_model = psat_models.PsatExam
    unit_model = psat_models.PsatUnit
    department_model = psat_models.PsatDepartment
    location_model = psat_models.PsatLocation
    student_model = psat_models.PsatStudent
    answer_count_model = psat_models.PsatAnswerCount
    student_form = forms.PsatStudentForm

    @property
    def url_answer_input(self):
        kwargs_dict = [
            {
                'exam_year': self.exam_year, 'exam_exam': self.exam_exam,
                'exam_round': self.exam_round, 'subject_field': field,
            } for field in self.subject_fields
        ]
        return [
            reverse('predict:answer-input', kwargs=kwargs)
            for kwargs in kwargs_dict
        ]

    @property
    def sub_title(self):
        default = {
            '프모': f'제{self.exam_round}회 프라임모의고사 합격 예측',
            '행시': f'{self.exam_year}년 5급공채 등 합격 예측',
            '칠급': f'{self.exam_year}년 7급공채 등 합격 예측',
        }
        return default[self.exam_exam]

    @property
    def sub_list(self):
        default = ['헌법', '언어', '자료', '상황']
        if self.exam_exam == '칠급':
            default.remove('헌법')
        return default

    @property
    def subject_list(self):
        default = ['헌법', '언어논리', '자료해석', '상황판단']
        if self.exam_exam == '칠급':
            default.remove('헌법')
        return default

    @property
    def subject_vars(self):
        default = {
            '헌법': ('헌법', 'heonbeob'), '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
            '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
        }
        if self.exam_exam == '칠급':
            default.pop('헌법')
        return default

    @property
    def subject_fields(self):
        default = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']
        if self.exam_exam == '칠급':
            default.remove('heonbeob')
        return default

    @property
    def score_fields(self):
        default = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg']
        if self.exam_exam == '칠급':
            default.remove('heonbeob')
        return default

    @property
    def admin_score_fields(self):
        default = ['psat_avg', 'heonbeob', 'eoneo', 'jaryo', 'sanghwang']
        if self.exam_exam == '칠급':
            default.remove('heonbeob')
        return default

    @property
    def field_vars(self):
        default = {
            'heonbeob': ('헌법', '헌법'), 'eoneo': ('언어', '언어논리'), 'jaryo': ('자료', '자료해석'),
            'sanghwang': ('상황', '상황판단'), 'psat_avg': ('평균', 'PSAT 평균'),
        }
        if self.exam_exam == '칠급':
            default.pop('heonbeob')
        return default

    @property
    def problem_count(self):
        count = 25 if self.exam_exam == '칠급' else 40
        default = {'heonbeob': 25, 'eoneo': count, 'jaryo': count, 'sanghwang': count}
        if self.exam_exam == '칠급':
            default.pop('heonbeob')
        return default

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
            'prefix_submit': [f'{fld}_submit' for fld in self.subject_fields],
            'prefix_predict': [f'{fld}_predict' for fld in self.subject_fields],
            'url_answer_input': self.url_answer_input,
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
class PoliceExamVars(ExamVars):
    selection: str = 'minbeob'

    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    avg_field = 'sum'

    @property
    def sum_fields(self):
        return ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', self.selection]

    exam_model = police_models.PoliceExam
    unit_model = police_models.PoliceUnit
    department_model = police_models.PoliceDepartment
    location_model = None
    student_model = police_models.PoliceStudent
    answer_count_model = police_models.PoliceAnswerCount
    student_form = forms.PoliceStudentForm

    @property
    def url_answer_input(self):
        kwargs_dict = [
            {
                'exam_year': self.exam_year, 'exam_exam': self.exam_exam,
                'exam_round': self.exam_round, 'subject_field': field,
            } for field in self.subject_fields
        ]
        return [
            reverse('predict:answer-input', kwargs=kwargs)
            for kwargs in kwargs_dict
        ]

    @property
    def sub_title(self):
        default = {
            '프모': f'제{self.exam_round}회 프라임모의고사 합격 예측',
            '경위': f'{self.exam_year}년 경위공채 합격 예측',
        }
        return default[self.exam_exam]

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
    def admin_score_fields(self):
        return ['sum', 'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', self.selection]

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
            'url_answer_input': self.url_answer_input,
        }

    def get_empty_data_answer(self):
        return [
            [
                {'no': no, 'ans': 0, 'field': fld} for no in range(1, self.problem_count[fld] + 1)
            ] for fld in self.subject_fields
        ]

    def get_field_idx(self, field):
        return self.subject_fields.index(field)
