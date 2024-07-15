from copy import deepcopy

from django.db.models import F
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models
from .. import utils

INFO = {'menu': 'predict', 'view_type': 'predict'}

EXAM_YEAR = 2024
EXAM_EXAM = '행시'
EXAM_ROUND = 0
EXAM_INFO = {'year': EXAM_YEAR, 'exam': EXAM_EXAM, 'round': EXAM_ROUND}
STUDENT_EXAM_INFO = {
    'student__year': EXAM_YEAR, 'student__exam': EXAM_EXAM, 'student__round': EXAM_ROUND}
SUB_TITLE_DICT = {
    '프모': f'제{EXAM_ROUND}회 프라임모의고사 성적 예측',
    '행시': f'{EXAM_YEAR}년 5급공채 합격 예측',
    '칠급': f'{EXAM_YEAR}년 7급공채 합격 예측',
}
SUB_TITLE = SUB_TITLE_DICT[EXAM_EXAM]

# Variables
SUB_LIST: list[str] = ['헌법', '언어', '자료', '상황']
SUBJECT_LIST: list[str] = ['헌법', '언어논리', '자료해석', '상황판단']
SUBJECT_VARS: dict[str, tuple] = {
    '헌법': ('헌법', 'heonbeob'),
    '언어': ('언어논리', 'eoneo'),
    '자료': ('자료해석', 'jaryo'),
    '상황': ('상황판단', 'sanghwang'),
    '평균': ('PSAT 평균', 'psat_avg'),
}
SUBJECT_FIELDS: list[str] = [SUBJECT_VARS[sub][1] for sub in SUB_LIST]
SCORE_FIELDS: list[str] = [value[1] for value in SUBJECT_VARS.values()]
FIELD_VARS: dict[str, tuple] = {
    value[1]: (key, value[0]) for key, value in SUBJECT_VARS.items()
}
DEFAULT_COUNT: int = 25 if EXAM_EXAM == '칠급' else 40
PROBLEM_COUNT: dict[str, int] = {
    SUBJECT_VARS[sub][1]: 25 if sub == '헌법' else DEFAULT_COUNT for sub in SUB_LIST
}
COUNT_FIELDS = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5']
SCORE_TEMPLATE_TABLE_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
SCORE_TEMPLATE_TABLE_2 = 'a_predict/snippets/index_sheet_score_table_2.html'

# Customize PROBLEM_COUNT, SUBJECT_VARS by EXAM_EXAM
if EXAM_EXAM == '칠급':
    SUB_LIST.remove('헌법')
    SUBJECT_LIST.remove('헌법')
    SUBJECT_VARS.pop('헌법')
    SUBJECT_FIELDS.remove('heonbeob')
    SCORE_FIELDS.remove('heonbeob')
    FIELD_VARS.pop('heonbeob')
    PROBLEM_COUNT.pop('heonbeob')

EXAM_VARS = {
    'year': EXAM_YEAR, 'exam': EXAM_EXAM, 'round': EXAM_ROUND, 'exam_info': EXAM_INFO,
    'sub_list': SUB_LIST, 'subject_list': SUBJECT_LIST,
    'subject_fields': SUBJECT_FIELDS, 'score_fields': SCORE_FIELDS,
    'subject_vars': SUBJECT_VARS, 'field_vars': FIELD_VARS,
    'problem_count': PROBLEM_COUNT, 'count_fields': COUNT_FIELDS,
    'exam_model': models.PsatExam, 'unit_model': models.PsatUnit,
    'department_model': models.PsatDepartment, 'location_model': models.PsatLocation,
    'student_model': models.PsatStudent, 'answer_count_model': models.PsatAnswerCount,

    'icon_subject': [icon_set_new.ICON_SUBJECT[sub] for sub in SUB_LIST],

    'info_tab_id': '01234',

    'answer_tab_id': ''.join([str(i) for i in range(len(SUB_LIST))]),
    'answer_tab_title': SUB_LIST,
    'prefix_as': [f'{field}_submit' for field in SUBJECT_FIELDS],
    'prefix_ap': [f'{field}_predict' for field in SUBJECT_FIELDS],

    'score_tab_id': '012',
    'score_tab_title': ['내 성적', '전체 기준', '직렬 기준'],
    'prefix_sa': ['my_all', 'total_all', 'department_all'],
    'prefix_sf': ['my_filtered', 'total_filtered', 'department_filtered'],
    'score_template': [SCORE_TEMPLATE_TABLE_1, SCORE_TEMPLATE_TABLE_2, SCORE_TEMPLATE_TABLE_2],
}


def list_view(request: HtmxHttpRequest):
    qs_exam = models.PsatExam.objects.order_by('id')
    qs_student = models.PsatStudent.objects.annotate(username=F('user__username')).order_by('id')
    exam_page_obj, exam_page_range = utils.get_page_obj_and_range(qs_exam)
    student_page_obj, student_page_range = utils.get_page_obj_and_range(qs_student)
    base_url = reverse_lazy('predict_new:admin-list')
    context = update_context_data(
        # base info
        info=INFO, title='Predict',
        sub_title='성적 예측 [관리자 페이지]',
        exam_list=qs_exam,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],

        # exam_list
        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,

        # student_list
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
        student_pagination_url=f'{base_url}?',
    )
    if request.htmx:
        return render(request, 'a_predict/admin_list.html#list_main', context)
    return render(request, 'a_predict/admin_list.html', context)


def detail_view(request: HtmxHttpRequest, pk: int):
    exam = get_object_or_404(models.PsatExam, pk=pk)
    exam_info = {'year': exam.year, 'exam': exam.exam, 'round': exam.round}
    admin_score_fields = ['department'] + [SCORE_FIELDS[-1]]
    admin_score_fields.extend(SCORE_FIELDS[:-1])
    admin_score_field_vars = deepcopy(FIELD_VARS)
    admin_score_field_vars['department'] = ('전체', 'department')

    participants = exam.participants
    statistics = exam.statistics

    qs_department = models.PsatDepartment.objects.filter(exam=exam.exam).order_by('id')
    departments = [{'id': 'total', 'unit': '', 'department': '전체'}]
    departments.extend(qs_department.values('id', 'unit', department=F('name')))

    stat_data: dict[str, list[list[dict]]] = {
        'all': [
            [
                {} for _ in admin_score_fields
            ] for _ in departments
        ],
        'filtered': [
            [
                {} for _ in admin_score_fields
            ] for _ in departments
        ],
    }
    for category in ['all', 'filtered']:
        for department_idx, department in enumerate(departments):
            for field_idx, field in enumerate(admin_score_fields):
                sub, subject = admin_score_field_vars[field]
                department_id = str(department['id'])
                if field == 'department':
                    stat_data[category][department_idx][field_idx] = department
                else:
                    if statistics[category][department_id][field]:
                        stat_data[category][department_idx][field_idx] = {
                            'field': field, 'sub': sub, 'subject': subject,
                            'participants': participants[category][department_id][field],
                            'max': statistics[category][department_id][field]['max'],
                            't10': statistics[category][department_id][field]['t10'],
                            't20': statistics[category][department_id][field]['t20'],
                            'avg': statistics[category][department_id][field]['avg'],
                        }
    stat_all_page_obj, stat_all_page_range = utils.get_page_obj_and_range(stat_data['all'])
    stat_filtered_page_obj, stat_filtered_page_range = utils.get_page_obj_and_range(stat_data['filtered'])

    qs_answer_count = models.PsatAnswerCount.objects.filter(
        **exam_info).order_by('number').values('subject', 'number', 'all', 'filtered')
    answer_count_all_by_subject = [
        [
            {'no': no} for no in range(1, problem_count + 1)
        ] for field, problem_count in PROBLEM_COUNT.items()
    ]

    # answer_count_all_by_subject = [
    #     [
    #         answer_count for answer_count in qs_answer_count
    #         if qs_answer_count['subject'] == field and
    #     ] for field in SUBJECT_FIELDS
    # ]

    answer_count = {
        field: [
            models.PsatAnswerCount.objects.filter(
                **exam_info, subject=field).order_by('number')
        ] for field in SUBJECT_FIELDS
    }

    context = update_context_data(
        # base info
        info=INFO, exam=exam, title='Predict',
        sub_title=utils.get_sub_title(exam),

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        answer_count=answer_count,
        # statistics
        stat_all_page_obj=stat_all_page_obj,
        stat_all_page_range=stat_all_page_range,
        stat_all_pagination_url=f'?',

        stat_filtered_page_obj=stat_filtered_page_obj,
        stat_filtered_page_range=stat_filtered_page_range,
        stat_filtered_pagination_url=f'?',
        #
        # # answer count analysis
        # heonbeob_page_obj=heonbeob_page_obj,
        # heonbeob_page_range=heonbeob_page_range,
        # heonbeob_pagination_url=self.get_url('answer_count_heonbeob'),
        #
        # # catalog
        # catalog_page_obj=catalog_page_obj,
        # catalog_page_range=catalog_page_range,
        # catalog_pagination_url=self.get_url('catalog'),
    )
    if request.htmx:
        return render(request, 'a_predict/admin_detail.html#admin_main', context)
    return render(request, 'a_predict/admin_detail.html', context)
