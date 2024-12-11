import dataclasses

from django.db.models import Case, When, Value, BooleanField, Count, F
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy

from common.constants import icon_set_new
from common.decorators import only_staff_allowed
from common.utils import HtmxHttpRequest, update_context_data
from scripts.update_prime_result_models import bulk_create_or_update
from .. import models, utils, forms

INFO = {'menu': 'score', 'view_type': 'primeScore'}


class ViewConfiguration:
    menu = menu_eng = 'prime'
    menu_kor = '프라임'
    submenu = submenu_eng = 'score'
    submenu_kor = '관리자 메뉴'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_psat_changelist')
    url_list = reverse_lazy('prime:score-admin-list')


@only_staff_allowed()
def list_view(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam_list = models.Psat.objects.filter(year=2024)
    config = ViewConfiguration()
    exam_page_obj, exam_page_range = utils.get_paginator_data(exam_list, page_number)

    student_list = models.ResultRegistry.objects.select_related('user', 'student').order_by('id')
    student_page_obj, student_page_range = utils.get_paginator_data(student_list, page_number)

    context = update_context_data(
        config=config,
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        exam_page_obj=exam_page_obj,
        exam_page_range=exam_page_range,
        student_page_obj=student_page_obj,
        student_page_range=student_page_range,
    )
    if view_type == 'student_list':
        return render(request, 'a_prime/score_admin_list.html#student_list', context)
    return render(request, 'a_prime/score_admin_list.html', context)


@only_staff_allowed()
def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', 1)

    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)
    config = ViewConfiguration()
    student_list = models.ResultStudent.objects.filter(psat=exam).select_related(
        'psat', 'category', 'score', 'rank_total', 'rank_category'
    ).order_by('psat__year', 'psat__round', 'rank_total__average')
    catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)

    data_statistics = models.ResultStatistics.objects.filter(psat=exam).order_by('id')

    qs_problems = models.Problem.objects.filter(psat=exam).order_by('subject', 'number').select_related(
        'result_answer_count',
        'result_answer_count_top_rank',
        'result_answer_count_mid_rank',
        'result_answer_count_low_rank',
    )
    data_answers = exam_vars.get_data_answers(qs_problems)

    context = update_context_data(
        config=config,
        exam=exam,
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,
        icon_search=icon_set_new.ICON_SEARCH,

        answer_tab=exam_vars.get_answer_tab,

        catalog_page_obj=catalog_page_obj,
        catalog_page_range=catalog_page_range,

        data_statistics=data_statistics,
        data_answers=data_answers,
    )
    if view_type == 'catalog_list':
        return render(request, 'a_prime/snippets/admin_detail_catalog.html', context)
    return render(request, 'a_prime/score_admin_detail.html', context)


@only_staff_allowed()
def update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')

    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam)

    is_answer_official = view_type == 'answer_official'
    is_statistics = view_type == 'statistics'

    context = {}
    next_url = exam.get_admin_detail_url()
    if is_answer_official:
        is_updated, message = update_answer_official(request, exam_vars, exam)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)
    if is_statistics:
        data_statistics = exam_vars.get_data_statistics()
        is_updated, message = exam_vars.update_statistics(data_statistics)
        print(is_updated)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_prime/snippets/admin_modal_update.html', context)


def print_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/score_admin_list.html', context)


def individual_student_print_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/score_admin_list.html', context)


def export_transcript_to_pdf_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/score_admin_list.html', context)


def export_statistics_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/score_admin_list.html', context)


def export_analysis_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/score_admin_list.html', context)


def export_scores_to_excel_view(request: HtmxHttpRequest):
    context = update_context_data()
    return render(request, 'a_prime/score_admin_list.html', context)


@dataclasses.dataclass
class ExamVars:
    exam: models.Psat

    exam_model = models.Psat
    statistics_model = models.ResultStatistics
    student_model = models.ResultStudent
    answer_model = models.ResultAnswer
    answer_count_model = models.ResultAnswerCount
    score_model = models.ResultScore
    rank_total_model = models.ResultRankTotal
    rank_category_model = models.ResultRankCategory
    student_form = forms.PrimePsatStudentForm

    sub_list = ['헌법', '언어', '자료', '상황']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    problem_count = {'헌법': 25, '언어': 40, '자료': 40, '상황': 40}
    subject_vars = {
        '헌법': ('헌법', 'subject_0'),
        '언어': ('언어논리', 'subject_1'),
        '자료': ('자료해석', 'subject_2'),
        '상황': ('상황판단', 'subject_3'),
        '평균': ('PSAT 평균', 'average'),
    }
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }

    # Template constants
    score_template_table_1 = 'a_prime/snippets/detail_sheet_score_table_1.html'
    score_template_table_2 = 'a_prime/snippets/detail_sheet_score_table_2.html'

    def get_student(self, user):
        return (
            self.student_model.objects.filter(registries__user=user, psat=self.exam)
            .select_related('psat', 'score', 'category').order_by('id').last()
        )

    def get_qs_student_answer(self, student):
        return models.ResultAnswer.objects.filter(
            problem__psat=self.exam, student=student).annotate(
            is_correct=Case(
                When(answer=F('problem__answer'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).select_related(
            'problem',
            'problem__result_answer_count',
            'problem__result_answer_count_top_rank',
            'problem__result_answer_count_mid_rank',
            'problem__result_answer_count_low_rank',
        )

    def get_qs_answers(self, student: models.ResultStudent, stat_type: str):
        qs_answers = (
            self.answer_model.objects.filter(problem__psat=self.exam).values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        if stat_type == 'department':
            qs_answers = qs_answers.filter(student__category__department=student.category.department)
        return qs_answers

    def get_qs_score(self, student: models.ResultStudent, stat_type: str):
        qs_score = self.score_model.objects.filter(student__psat=self.exam)
        if stat_type == 'department':
            qs_score = qs_score.filter(student__category__department=student.category.department)
        return qs_score.values()

    def get_score_frequency_list(self) -> list:
        return self.student_model.objects.filter(psat=self.exam).values_list('score__sum', flat=True)

    def get_score_tab(self):
        return [
            {'id': '0', 'title': '내 성적', 'template': self.score_template_table_1},
            {'id': '1', 'title': '전체 기준', 'template': self.score_template_table_2},
            {'id': '2', 'title': '직렬 기준', 'template': self.score_template_table_2},
        ]

    def get_answer_tab(self):
        answer_tab = [
            {'id': str(idx), 'title': sub, 'icon': icon_set_new.ICON_SUBJECT[sub], 'answer_count': 5}
            for idx, sub in enumerate(self.sub_list)
        ]
        answer_tab[0]['answer_count'] = 4
        return answer_tab

    def get_empty_data_answer(self):
        return [[] for _ in self.sub_list]

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

    def get_data_answers(self, qs_problems):
        data_answers = self.get_empty_data_answer()

        for line in qs_problems:
            sub = line.subject
            idx = self.sub_list.index(sub)
            field = self.subject_vars[sub][1]
            ans_official = line.answer

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            line.no = line.number
            line.ans_official = ans_official
            line.ans_list = answer_official_list
            line.field = field

            line.rate_correct = line.result_answer_count.get_answer_rate(ans_official)
            line.rate_correct_top = line.result_answer_count_top_rank.get_answer_rate(ans_official)
            line.rate_correct_mid = line.result_answer_count_mid_rank.get_answer_rate(ans_official)
            line.rate_correct_low = line.result_answer_count_low_rank.get_answer_rate(ans_official)
            line.rate_gap = line.rate_correct_top - line.rate_correct_low

            data_answers[idx].append(line)
        return data_answers

    def get_data_statistics(self):
        qs_students = (
            self.student_model.objects.filter(psat=self.exam)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_total')
            .annotate(
                department=F('category__department'),
                subject_0=F('score__subject_0'),
                subject_1=F('score__subject_1'),
                subject_2=F('score__subject_2'),
                subject_3=F('score__subject_3'),
                average=F('score__average'),
            )
        )

        departments = models.choices.get_departments()
        departments.insert(0, '전체')

        data_statistics = []
        score_list = {}
        for department in departments:
            data_statistics.append({'department': department, 'participants': 0})
            score_list.update({
                department: {field: [] for field, subject_tuple in self.field_vars.items()}
            })

        for qs in qs_students:
            for field, subject_tuple in self.field_vars.items():
                score = getattr(qs, field)
                score_list['전체'][field].append(score)
                score_list[qs.department][field].append(score)

        for department, score_dict in score_list.items():
            department_idx = departments.index(department)
            for field, scores in score_dict.items():
                sub = self.field_vars[field][0]
                subject = self.field_vars[field][1]
                participants = len(scores)

                sorted_scores = sorted(scores, reverse=True)
                max_score = top_score_10 = top_score_20 = avg_score = None
                if sorted_scores:
                    max_score = sorted_scores[0]
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    top_score_10 = sorted_scores[top_10_threshold - 1]
                    top_score_20 = sorted_scores[top_20_threshold - 1]
                    avg_score = sum(scores) / participants

                data_statistics[department_idx][field] = {
                    'field': field,
                    'is_confirmed': True,
                    'sub': sub,
                    'subject': subject,
                    'icon': icon_set_new.ICON_SUBJECT[sub],
                    'participants': participants,
                    'max': max_score,
                    't10': top_score_10,
                    't20': top_score_20,
                    'avg': avg_score,
                }
        return data_statistics

    def update_statistics(self, data_statistics):
        list_update = []
        list_create = []

        for data_stat in data_statistics:
            department = data_stat['department']
            stat_dict = {'department': department}
            for field in self.field_vars.keys():
                stat_dict.update({
                    field: {
                        'participants': data_stat[field]['participants'],
                        'max': data_stat[field]['max'],
                        't10': data_stat[field]['t10'],
                        't20': data_stat[field]['t20'],
                        'avg': data_stat[field]['avg'],
                    }
                })

            try:
                new_query = self.statistics_model.objects.get(psat=self.exam, department=department)
                fields_not_match = any(
                    getattr(new_query, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except self.statistics_model.DoesNotExist:
                list_create.append(self.statistics_model(psat=self.exam, **stat_dict))
        update_fields = [
            'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average',
        ]
        bulk_create_or_update(self.statistics_model, list_create, list_update, update_fields)

        is_updated = True
        message = '통계가 업데이트됐습니다.'

        return is_updated, message
