import dataclasses

from django.urls import reverse

from common.constants import icon_set_new
from .. import models, forms


@dataclasses.dataclass
class PsatExamVars:
    info = {'menu': 'predict', 'view_type': 'predict'}

    exam_year: int = 0
    exam_exam: str = ''
    exam_round: int = 0

    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5']
    avg_field = 'psat_avg'
    sum_fields = ['eoneo', 'jaryo', 'sanghwang']

    exam_model = models.PsatExam
    unit_model = models.PsatUnit
    department_model = models.PsatDepartment
    location_model = models.PsatLocation
    student_model = models.PsatStudent
    answer_count_model = models.PsatAnswerCount
    student_form = forms.StudentForm

    score_template_table_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
    score_template_table_2 = 'a_predict/snippets/index_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'prefix_all': ['my_all', 'total_all', 'department_all'],
        'prefix_filtered': ['my_filtered', 'total_filtered', 'department_filtered'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'exam': self.exam_exam, 'round': self.exam_round}

    @property
    def exam_url_kwargs(self):
        return {'exam_year': self.exam_year, 'exam_exam': self.exam_exam, 'exam_round': self.exam_round}

    @property
    def url_index(self):
        return reverse('predict_new:index')

    @property
    def url_detail(self):
        return reverse('predict_new:psat-detail', kwargs=self.exam_url_kwargs)

    @property
    def url_update_info_answer(self):
        return reverse('predict_new:update-info-answer', kwargs=self.exam_url_kwargs)

    @property
    def url_update_answer_predict(self):
        return reverse('predict_new:update-answer-predict', kwargs=self.exam_url_kwargs)

    @property
    def url_update_answer_submit(self):
        return reverse('predict_new:update-answer-submit', kwargs=self.exam_url_kwargs)

    @property
    def url_update_score(self):
        return reverse('predict_new:update-score', kwargs=self.exam_url_kwargs)

    @property
    def url_answer_input(self):
        kwargs_dict = [
            {
                'exam_year': self.exam_year, 'exam_exam': self.exam_exam,
                'exam_round': self.exam_round, 'subject_field': field,
            } for field in self.subject_fields
        ]
        return [
            reverse('predict_new:answer-input', kwargs=kwargs)
            for kwargs in kwargs_dict
        ]

    def get_url_answer_submit(self, subject_field):
        kwargs = {
            'exam_year': self.exam_year, 'exam_exam': self.exam_exam,
            'exam_round': self.exam_round, 'subject_field': subject_field,
        }
        return reverse('predict_new:answer-submit', kwargs=kwargs)

    def get_url_answer_confirm(self, subject_field):
        kwargs = {
            'exam_year': self.exam_year, 'exam_exam': self.exam_exam,
            'exam_round': self.exam_round, 'subject_field': subject_field,
        }
        return reverse('predict_new:answer-confirm', kwargs=kwargs)

    @property
    def student_exam_info(self):
        return {
            'student__year': self.exam_year, 'student__exam': self.exam_exam, 'student__round': self.exam_round
        }

    @property
    def sub_title(self):
        default = {
            '프모': f'제{self.exam_round}회 프라임모의고사 성적 예측',
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
            'prefix_submit': [f'{field}_submit' for field in self.subject_fields],
            'prefix_predict': [f'{field}_predict' for field in self.subject_fields],
            'url_answer_input': self.url_answer_input,
        }

    def get_empty_data_answer(self):
        return [
            [
                {'no': no, 'ans': 0, 'field': field} for no in range(1, self.problem_count[field] + 1)
            ] for field in self.subject_fields
        ]

    def get_field_idx(self, field):
        return self.subject_fields.index(field)
