import dataclasses
from typing import Type

import pandas as pd
from django.db.models import QuerySet
from django.urls import reverse

from common.constants import icon_set_new
from .. import forms
from ..forms import PsatStudentForm, PoliceStudentForm
from ..models import psat_models, police_models, PsatExam, PoliceExam, PsatUnit, PoliceUnit, PsatDepartment, \
    PoliceDepartment, PsatStudent, PoliceStudent, PsatAnswerCount, PoliceAnswerCount
import a_predict.models as models


@dataclasses.dataclass
class ExamVars:
    exam_year: int
    exam_exam: str
    exam_round: int

    # Obj and queryset derived from views
    exam: psat_models.PsatExam | police_models.PoliceExam = None
    student: psat_models.PsatStudent | police_models.PoliceStudent = None
    location: psat_models.Location = None
    qs_answer_count = None
    qs_student = None
    qs_department = None

    # Template variables
    data_answer_predict: list[list[dict]] = dataclasses.field(default_factory=list)
    answer_confirmed: list[bool] = dataclasses.field(default_factory=list)
    data_answer_official_tuple: tuple[list[list[dict]], bool] = dataclasses.field(default_factory=tuple)
    data_answer_student: list[list[dict]] = dataclasses.field(default_factory=list)
    info_answer_student: list = dataclasses.field(default_factory=list)
    stat: dict[str, list[dict]] = dataclasses.field(default_factory=dict)

    # Template constants
    info = {'menu': 'predict', 'view_type': 'predict'}
    icon_menu = icon_set_new.ICON_MENU['predict']
    score_template_table_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
    score_template_table_2 = 'a_predict/snippets/index_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'exam': self.exam_exam, 'round': self.exam_round}

    def get_problem_info(self, field: str, number: int):
        return {
            'year': self.exam_year, 'exam': self.exam_exam, 'round': self.exam_round,
            'subject': field, 'number': number,
        }

    @property
    def exam_url_kwargs(self):
        return {'exam_year': self.exam_year, 'exam_exam': self.exam_exam, 'exam_round': self.exam_round}

    @property
    def url_index(self):
        return reverse('predict:index')

    @property
    def url_detail(self):
        return reverse('predict:detail', kwargs=self.exam_url_kwargs)

    @property
    def url_student_create(self):
        return reverse('predict:student-create', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_list(self):
        return reverse('predict:admin-list')

    @property
    def url_admin_detail(self):
        return reverse('predict:admin-detail', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_update(self):
        return reverse('predict:admin-update', kwargs=self.exam_url_kwargs)

    @property
    def student_exam_info(self):
        return {
            'student__year': self.exam_year, 'student__exam': self.exam_exam, 'student__round': self.exam_round
        }


@dataclasses.dataclass
class PsatExamVars(ExamVars):
    exam_type: str = 'psat'

    exam_model = psat_models.PsatExam
    unit_model = psat_models.PsatUnit
    department_model = psat_models.PsatDepartment
    location_model = psat_models.PsatLocation
    student_model = psat_models.PsatStudent
    answer_count_model = psat_models.PsatAnswerCount
    student_form = forms.PsatStudentForm

    # Answer count fields constant
    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5']
    all_count_fields = count_fields + ['count_multiple', 'count_total']

    def get_count_default(self):
        return {fld: 0 for fld in self.all_count_fields}

    # Sum or average fields
    avg_field = 'psat_avg'
    sum_fields = ['eoneo', 'jaryo', 'sanghwang']

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
    def admin_subject_list(self):
        default = ['PSAT', '헌법', '언어논리', '자료해석', '상황판단']
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

    def get_subject_field(self, subject):
        for field, subject_tuple in self.field_vars.items():
            if field == subject:
                return field
            if subject_tuple[0] == subject:
                return field
            if subject_tuple[1] == subject:
                return field

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
    exam_type: str = 'police'
    selection: str = 'minbeob'

    exam_model = police_models.PoliceExam
    unit_model = police_models.PoliceUnit
    department_model = police_models.PoliceDepartment
    location_model = None
    student_model = police_models.PoliceStudent
    answer_count_model = police_models.PoliceAnswerCount
    student_form = forms.PoliceStudentForm

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
            '경위': f'74기 경위공채 합격 예측',
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


@dataclasses.dataclass
class AdminPoliceExamVars(PoliceExamVars):
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


@dataclasses.dataclass
class PredictExamVars:
    exam_type: str
    exam_year: int
    exam_exam: str
    exam_round: int
    file_name: str
    selection: str = ''
    is_admin: bool = False

    # common vars
    default_count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    extra_count_fields = ['count_multiple', 'count_total']
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']
    subject_to_field_dict = {
        '언어논리': 'eoneo', '자료해석': 'jaryo', '상황판단': 'sanghwang',
        '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
        '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
        '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    }
    field_to_subject_dict = {
        'eoneo': '언어논리', 'jaryo': '자료해석', 'sanghwang': '상황판단',
        'hyeongsa': '형사법', 'heonbeob': '헌법',  # 전체 공통
        'gyeongchal': '경찰학', 'beomjoe': '범죄학',  # 일반 필수
        'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙',  # 일반 선택
    }
    subject_vars = {
        '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
        '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
        '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
        '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
        '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
    }
    field_vars = {
        'eoneo': ('언어', '언어논리'), 'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'), 'psat_avg': ('평균', 'PSAT 평균'),
        'hyeongsa': ('형사', '형사학'), 'heonbeob': ('헌법', '헌법'),
        'gyeongchal': ('경찰', '경찰학'), 'beomjoe': ('범죄', '범죄학'),
        'haengbeob': ('행법', '행정법'), 'haenghag': ('행학', '행정학'), 'minbeob': ('민법', '민법총칙'),
    }

    info = {'menu': 'predict', 'view_type': 'predict'}
    icon_menu = icon_set_new.ICON_MENU['predict']
    score_template_table_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
    score_template_table_2 = 'a_predict/snippets/index_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }

    # psat/police vars
    only_psat_fields = ['eoneo', 'jaryo', 'sanghwang']
    police_common_fields = ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']

    @property
    def is_psat(self) -> bool:
        return self.exam_type == 'psat'

    @property
    def exam_model(self) -> Type[PsatExam | PoliceExam]:
        if self.is_psat:
            return models.PsatExam
        return models.PoliceExam

    @property
    def unit_model(self) -> Type[PsatUnit | PoliceUnit]:
        if self.is_psat:
            return models.PsatUnit
        return models.PoliceUnit

    @property
    def department_model(self) -> Type[PsatDepartment | PoliceDepartment]:
        if self.is_psat:
            return models.PsatDepartment
        return models.PoliceDepartment

    @property
    def student_model(self) -> Type[PsatStudent | PoliceStudent]:
        if self.is_psat:
            return models.PsatStudent
        return models.PoliceStudent

    @property
    def answer_count_model(self) -> Type[PsatAnswerCount | PoliceAnswerCount]:
        if self.is_psat:
            return models.PsatAnswerCount
        return models.PoliceAnswerCount

    @property
    def student_form(self) -> Type[PsatStudentForm | PoliceStudentForm]:
        if self.is_psat:
            return forms.PsatStudentForm
        return forms.PoliceStudentForm

    @property
    def exam_info(self) -> dict:
        return {'year': self.exam_year, 'exam': self.exam_exam, 'round': self.exam_round}

    @property
    def student_exam_info(self):
        return {
            'student__year': self.exam_year, 'student__exam': self.exam_exam, 'student__round': self.exam_round
        }

    @property
    def exam_url_kwargs(self):
        return {
            'exam_type': self.exam_type, 'exam_year': self.exam_year,
            'exam_exam': self.exam_exam, 'exam_round': self.exam_round
        }

    @property
    def exam(self) -> Type[PsatExam | PoliceExam]:
        return self.exam_model.objects.filter(**self.exam_info).first()

    @property
    def all_units(self) -> Type[PsatExam | PoliceExam]:
        return self.unit_model.objects.filter(exam=self.exam_exam).first()

    @property
    def all_departments(self) -> Type[PsatDepartment | PoliceDepartment]:
        return self.department_model.objects.filter(**self.exam_info)

    @property
    def qs_student(self) -> QuerySet:
        return self.student_model.objects.filter(**self.exam_info)

    @property
    def sub_list(self):
        if self.is_psat:
            if self.exam_exam == '칠급':
                return ['언어', '상황', '자료']
            return ['헌법', '언어', '자료', '상황']
        police_common_sub_list = ['형사', '헌법', '경찰', '범죄']
        default = {'haengbeob': '행법', 'haenghag': '행학', 'minbeob': '민법'}
        return police_common_sub_list + [default[self.selection]]

    @property
    def subject_list(self):
        chilgeup = ['언어논리', '상황판단', '자료해석']
        haengsi = ['헌법', '언어논리', '자료해석', '상황판단']
        if self.is_psat:
            if self.is_admin:
                return ['PSAT'] + self.subject_list
            else:
                if self.exam_exam == '칠급':
                    return chilgeup
                return haengsi
        police_common = ['형사학', '헌법', '경찰학', '범죄학']
        if self.is_admin:
            return ['총점'] + police_common + ['민법총칙', '행정학', '행정법']
        else:
            default = {'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙'}
            return police_common + [default[self.selection]]

    @property
    def answer_fields(self) -> list:
        if self.is_psat:
            if self.exam_exam == '행시':
                return ['eoneo', 'sanghwang', 'jaryo']
            return ['heonbeob'] + self.only_psat_fields
        return self.police_common_fields + [self.selection]

    @property
    def all_subject_fields(self) -> list:
        if self.is_psat:
            return self.answer_fields
        return self.police_common_fields + ['minbeob', 'haenghag', 'haengbeob']

    @property
    def selection_choice(self):
        return [
            {'field': 'minbeob', 'name': '민법총칙'},
            {'field': 'haenghag', 'name': '행정학'},
            {'field': 'haengbeob', 'name': '행정법'},
        ]

    @property
    def final_field(self) -> str:
        return 'psat_avg' if self.is_psat else 'sum'

    @property
    def score_fields(self) -> list:
        if self.is_admin:
            return [self.final_field] + self.answer_fields
        return self.answer_fields + [self.final_field]

    @property
    def count_fields(self) -> list:
        default_count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
        if self.is_psat:
            return default_count_fields + ['count_5']
        return default_count_fields

    @property
    def all_count_fields(self) -> list:
        return self.count_fields + ['count_multiple', 'count_total']

    @property
    def url_index(self):
        return reverse('predict:index')

    @property
    def url_detail(self):
        return reverse('predict:detail', kwargs=self.exam_url_kwargs)

    @property
    def url_student_create(self):
        return reverse('predict:student-create', kwargs=self.exam_url_kwargs)

    @property
    def url_answer_input(self):
        kwargs_dict = [
            dict(self.exam_url_kwargs, **{'subject_field': fld}) for fld in self.answer_fields
        ]
        return [
            reverse('predict:answer-input', kwargs=kwargs) for kwargs in kwargs_dict
        ]

    @property
    def url_admin_list(self):
        return reverse('predict:admin-list')

    @property
    def url_admin_detail(self):
        return reverse('predict:admin-detail', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_update(self):
        return reverse('predict:admin-update', kwargs=self.exam_url_kwargs)

    @property
    def sub_title(self):
        default = {
            'psat': {
                '프모': f'제{self.exam_round}회 프라임모의고사 합격 예측',
                '행시': f'{self.exam_year}년 5급공채 등 합격 예측',
                '칠급': f'{self.exam_year}년 7급공채 등 합격 예측',
            },
            'police': {
                '프모': f'제{self.exam_round}회 프라임모의고사 합격 예측',
                '경위': f'74기 경위공채 합격 예측',
            }
        }
        return default[self.exam_type][self.exam_exam]

    @property
    def icon_subject(self) -> list:
        if self.is_psat:
            return [icon_set_new.ICON_SUBJECT[sub] for sub in self.sub_list]
        return ['' for _ in self.sub_list]

    @property
    def info_tab(self):
        return {'id': ''.join([str(i) for i in range(len(self.answer_fields))])}

    @property
    def answer_tab(self):
        return {
            'id': ''.join([str(i) for i in range(len(self.sub_list))]),
            'title': self.sub_list,
            'url_answer_input': self.url_answer_input,
        }

    def get_problem_info(self, field: str, number: int) -> dict:
        return dict(self.exam_info, **{'subject': field, 'number': number})

    def get_subject_field(self, subject):
        for fld, sub_tuple in self.field_vars.items():
            if fld == subject or sub_tuple[0] == subject or sub_tuple[1] == subject:
                return fld

    def get_police_student_score_fields(self, selection) -> list:
        return self.police_common_fields + [selection] + [self.final_field]

    def get_problem_count(self, field) -> int:
        if self.is_psat:
            if self.exam_exam == '칠급' or field in ['heonbeob', '헌법']:
                return 25
        return 40

    def get_score_unit(self, field) -> float | int:
        if self.is_psat:
            if self.exam_exam == '칠급' or field in ['heonbeob', '헌법']:
                return 4
            return 2.5
        police_score_unit = {
            'hyeongsa': 3, 'gyeongchal': 3, 'sebeob': 2, 'hoegye': 2, 'jeongbo': 2,
            'sine': 2, 'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
        }
        return police_score_unit.get(field, 1.5)

    def get_empty_data_answer(self):
        return [
            [
                {'no': no, 'ans': 0, 'field': fld}
                for no in range(1, self.get_problem_count(fld) + 1)
            ] for fld in self.answer_fields
        ]

    def get_field_idx(self, field):
        return self.answer_fields.index(field)

    def get_answer_official(self) -> dict[str, list]:
        df = pd.read_excel(self.file_name, sheet_name='정답', header=0, index_col=0)
        df.fillna(value=0, inplace=True)
        answer_official = {}
        for subject, answers in df.items():
            field = self.get_field_name(subject)
            answer_official[field] = [int(ans) for ans in answers if ans]
        return answer_official

    def get_field_name(self, subject) -> str:
        return self.subject_to_field_dict[subject]

    def get_subject_name(self, field) -> str:
        return self.field_to_subject_dict[field]
