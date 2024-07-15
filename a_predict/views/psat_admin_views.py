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
RANK_LIST = ['all_rank', 'low_rank', 'mid_rank', 'top_rank']

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
    'rank_list': RANK_LIST,

    'exam_model': models.PsatExam, 'unit_model': models.PsatUnit,
    'department_model': models.PsatDepartment, 'location_model': models.PsatLocation,
    'student_model': models.PsatStudent, 'answer_count_model': models.PsatAnswerCount,

    'icon_subject': [icon_set_new.ICON_SUBJECT[sub] for sub in SUB_LIST],

    'info_tab_id': '01234',

    'answer_tab_id': ''.join([str(i) for i in range(len(SUB_LIST))]),
    'answer_tab_title': SUB_LIST,
    'prefix_aa': [f'{field}_all' for field in SUBJECT_FIELDS],
    'prefix_af': [f'{field}_filtered' for field in SUBJECT_FIELDS],

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

    stat_data = utils.get_admin_stat_data(exam_vars=EXAM_VARS, exam=exam)
    stat_page_data = [
        utils.get_page_obj_and_range(stat_data[cat]) for cat in ['all', 'filtered']
    ]
    stat_page_obj = [page_data[0] for page_data in stat_page_data]
    stat_page_range = [page_data[1] for page_data in stat_page_data]
    stat_pagination_url = ['?', '?']

    qs_answer_count = models.PsatAnswerCount.objects.filter(**exam_info).order_by('id')
    answer_predict = utils.get_data_answer_predict(exam_vars=EXAM_VARS, qs_answer_count=qs_answer_count)
    answer_count_data = utils.get_admin_answer_count_data(
        exam_vars=EXAM_VARS, exam=exam, answer_predict=answer_predict)
    answer_all_page_data = [
        utils.get_page_obj_and_range(answer_count_data['all'][i]) for i in range(4)
    ]
    answer_all_page_obj = [page_data[0] for page_data in answer_all_page_data]
    answer_all_page_range = [page_data[1] for page_data in answer_all_page_data]
    answer_all_pagination_url = ['?', '?', '?', '?']

    context = update_context_data(
        # base info
        info=INFO, exam=exam, title='Predict',
        sub_title=utils.get_sub_title(exam),
        exam_vars=EXAM_VARS,

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        # statistics
        stat_page_obj=stat_page_obj,
        stat_page_range=stat_page_range,
        stat_pagination_url=stat_pagination_url,

        # answer count analysis
        answer_all_page_obj=answer_all_page_obj,
        answer_all_page_range=answer_all_page_range,
        answer_all_pagination_url=answer_all_pagination_url,
        #
        # # catalog
        # catalog_page_obj=catalog_page_obj,
        # catalog_page_range=catalog_page_range,
        # catalog_pagination_url=self.get_url('catalog'),
    )
    if request.htmx:
        return render(request, 'a_predict/admin_detail.html#admin_main', context)
    return render(request, 'a_predict/admin_detail.html', context)
