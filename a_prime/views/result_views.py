import dataclasses
from collections import Counter

from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.db.models import F, Case, When, Value, BooleanField, Count
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, forms, utils


class ViewConfiguration:
    menu = menu_eng = 'prime'
    menu_kor = '프라임'
    submenu = submenu_eng = 'score'
    submenu_kor = '모의고사 성적 확인'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_psat_changelist')
    url_list = reverse_lazy('prime:result-list')
    url_predict_list = reverse_lazy('prime:predict-list')


def get_student_dict(user, exam_list):
    if user.is_authenticated:
        students = (
            models.ResultStudent.objects.filter(registries__user=user, psat__in=exam_list)
            .select_related('psat', 'score', 'category').order_by('id')
        )
        return {student.psat: student for student in students}
    return {}


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam_list = models.Psat.objects.filter(year=2025)

    subjects = [
        ('헌법', 'subject_0'),
        ('언어논리', 'subject_1'),
        ('자료해석', 'subject_2'),
        ('상황판단', 'subject_3'),
        ('PSAT 평균', 'average'),
    ]

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    student_dict = get_student_dict(request.user, exam_list)
    for obj in page_obj:
        obj: models.Psat
        obj.student = student_dict.get(obj, None)

    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        subjects=subjects,
        icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj,
        page_range=page_range
    )
    return render(request, 'a_prime/result_list.html', context)


def get_detail_context(user, exam: models.Psat, student=None):
    exam_vars = ExamVars(exam)
    config = ViewConfiguration()
    config.submenu_kor = f'제{exam.round}회 ' + config.submenu_kor

    if student is None:
        student = exam_vars.get_student(user)
        if not student:
            return None

    stat_total = exam_vars.get_dict_stat_data(student, 'total')
    stat_department = exam_vars.get_dict_stat_data(student, 'department')
    frequency_score = exam_vars.get_dict_frequency_score(student)
    qs_student_answer = exam_vars.get_qs_student_answer(student)
    data_answers = exam_vars.get_data_answers(qs_student_answer)

    context = update_context_data(
        current_time=timezone.now(),
        exam=exam,
        exam_vars=exam_vars,
        config=config,
        sub_title=f'제{exam.round}회 프라임모의고사 성적표',

        # icon
        icon_menu=icon_set_new.ICON_MENU,
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # tab variables for templates
        answer_tab=exam_vars.get_answer_tab,
        score_tab=exam_vars.get_score_tab,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_total=stat_total,
        stat_department=stat_department,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answers=data_answers,
    )
    return context


def detail_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    if timezone.now() < exam.score_opened_at:
        return redirect('prime:result-list')
    context = get_detail_context(request.user, exam)
    if context is None:
        return redirect('prime:result-list')
    return render(request, 'a_prime/result_detail.html', context)


def print_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    if timezone.now() < exam.score_opened_at:
        return redirect('prime:result-list')
    context = get_detail_context(request.user, exam)
    if context is None:
        return redirect('prime:result-list')
    return render(request, 'a_prime/result_print.html', context)


def modal_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    exam_vars = ExamVars(exam)
    view_type = request.headers.get('View-Type', '')

    form = exam_vars.student_form()
    context = update_context_data(exam=exam, form=form)
    if view_type == 'no_open':
        return render(request, 'a_prime/snippets/modal_result_no_open.html', context)

    if view_type == 'student_register':
        context = update_context_data(
            context,
            exam_vars=exam_vars,
            header=f'{exam.year}년 대비 제{exam.round}회 프라임 모의고사 수험 정보 입력',
        )
        return render(request, 'a_prime/snippets/modal_result_student_register.html', context)


@require_POST
def register_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    exam_vars = ExamVars(exam)

    form = exam_vars.student_form(data=request.POST, files=request.FILES)
    context = update_context_data(exam_vars=exam_vars, exam=exam, form=form)
    if form.is_valid():
        serial = form.cleaned_data['serial']
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        try:
            target_student = exam_vars.student_model.objects.get(
                psat=exam, serial=serial, name=name, password=password)
            registered_student, _ = exam_vars.registry_model.objects.get_or_create(
                user=request.user, student=target_student)
            context = update_context_data(context, user_verified=True)
        except exam_vars.student_model.DoesNotExist:
            context = update_context_data(context, no_student=True)

    return render(request, 'a_prime/snippets/modal_result_student_register.html#student_info', context)


@require_POST
def unregister_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    student = models.ResultRegistry.objects.get(student__psat=exam, user=request.user)
    student.delete()
    return redirect('prime:result-list')


@dataclasses.dataclass
class ExamVars:
    exam: models.Psat

    exam_model = models.Psat
    problem_model = models.Problem
    category_model = models.Category

    student_model = models.ResultStudent
    registry_model = models.ResultRegistry
    answer_model = models.ResultAnswer
    answer_count_model = models.ResultAnswerCount
    score_model = models.ResultScore
    rank_total_model = models.ResultRankTotal
    rank_category_model = models.ResultRankCategory

    student_form = forms.PrimeResultStudentForm

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
        annotate_dict = {
            'score_sum': F('score__sum'),
            'rank_tot_num': F(f'rank_total__participants'),
            'rank_dep_num': F(f'rank_category__participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'subject_2', 3: 'subject_3', 'avg': 'average'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = F(f'score__{fld}')
            annotate_dict[f'rank_tot_{key}'] = F(f'rank_total__{fld}')
            annotate_dict[f'rank_dep_{key}'] = F(f'rank_category__{fld}')

        return (
            self.student_model.objects.filter(registries__user=user, psat=self.exam)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .annotate(department=F('category__department'), **annotate_dict)
            .order_by('id').last()
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

    def get_qs_problems_for_answer_count(self, subject=None):
        annotate_dict = {}
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}'] = F(f'result_answer_count__{fld}')
            annotate_dict[f'{fld}_top'] = F(f'result_answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = F(f'result_answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = F(f'result_answer_count_low_rank__{fld}')
        qs_problems = (
            self.problem_model.objects.filter(psat=self.exam)
            .order_by('subject', 'number')
            .select_related(
                'result_answer_count',
                'result_answer_count_top_rank',
                'result_answer_count_mid_rank',
                'result_answer_count_low_rank',
            ).annotate(**annotate_dict)
        )
        if subject:
            qs_problems = qs_problems.filter(subject=subject)
        return qs_problems

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
        return [
            {'id': str(idx), 'title': sub, 'icon': icon_set_new.ICON_SUBJECT[sub]}
            for idx, sub in enumerate(self.sub_list)
        ]

    def get_empty_data_answer(self):
        return [[] for _ in self.sub_list]

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

    # def get_data_answers(self, qs_student_answer):
    #     for line in qs_student_answer:
    #         sub = line.problem.subject
    #         field = self.subject_vars[sub][1]
    #         ans_official = line.problem.answer
    #         ans_student = line.answer
    #
    #         answer_official_list = []
    #         if 1 <= ans_official <= 5:
    #             result = ans_student == ans_official
    #         else:
    #             answer_official_list = [int(digit) for digit in str(ans_official)]
    #             result = ans_student in answer_official_list
    #
    #         line.no = line.problem.number
    #         line.ans_official = ans_official
    #         line.ans_official_circle = line.problem.get_answer_display
    #         line.ans_student = ans_student
    #         line.ans_list = answer_official_list
    #         line.field = field
    #         line.result = result
    #
    #         line.rate_correct = line.problem.result_answer_count.get_answer_rate(ans_official)
    #         line.rate_correct_top = line.problem.result_answer_count_top_rank.get_answer_rate(ans_official)
    #         line.rate_correct_mid = line.problem.result_answer_count_mid_rank.get_answer_rate(ans_official)
    #         line.rate_correct_low = line.problem.result_answer_count_low_rank.get_answer_rate(ans_official)
    #         try:
    #             line.rate_gap = line.rate_correct_top - line.rate_correct_low
    #         except TypeError:
    #             line.rate_gap = None
    #
    #         line.rate_selection = line.problem.result_answer_count.get_answer_rate(ans_student)
    #         line.rate_selection_top = line.problem.result_answer_count_top_rank.get_answer_rate(ans_student)
    #         line.rate_selection_mid = line.problem.result_answer_count_mid_rank.get_answer_rate(ans_student)
    #         line.rate_selection_low = line.problem.result_answer_count_low_rank.get_answer_rate(ans_student)
    #
    #     return qs_student_answer

    def get_data_answers(self, qs_student_answer):
        data_answers = self.get_empty_data_answer()

        for line in qs_student_answer:
            sub = line.problem.subject
            idx = self.sub_list.index(sub)
            field = self.subject_vars[sub][1]
            ans_official = line.problem.answer
            ans_student = line.answer

            answer_official_list = []
            if 1 <= ans_official <= 5:
                result = ans_student == ans_official
            else:
                answer_official_list = [int(digit) for digit in str(ans_official)]
                result = ans_student in answer_official_list

            line.no = line.problem.number
            line.ans_official = ans_official
            line.ans_official_circle = line.problem.get_answer_display
            line.ans_student = ans_student
            line.ans_list = answer_official_list
            line.field = field
            line.result = result

            line.rate_correct = line.problem.result_answer_count.get_answer_rate(ans_official)
            line.rate_correct_top = line.problem.result_answer_count_top_rank.get_answer_rate(ans_official)
            line.rate_correct_mid = line.problem.result_answer_count_mid_rank.get_answer_rate(ans_official)
            line.rate_correct_low = line.problem.result_answer_count_low_rank.get_answer_rate(ans_official)
            line.rate_gap = line.rate_correct_top - line.rate_correct_low

            if ans_student <= 5:
                line.rate_selection = line.problem.result_answer_count.get_answer_rate(ans_student)
                line.rate_selection_top = line.problem.result_answer_count_top_rank.get_answer_rate(ans_student)
                line.rate_selection_mid = line.problem.result_answer_count_mid_rank.get_answer_rate(ans_student)
                line.rate_selection_low = line.problem.result_answer_count_low_rank.get_answer_rate(ans_student)

            data_answers[idx].append(line)
        return data_answers

    def get_dict_stat_data(self, student: models.ResultStudent, stat_type: str) -> dict:
        qs_answers = self.get_qs_answers(student, stat_type)
        qs_score = self.get_qs_score(student, stat_type)

        participants_dict = {
            self.subject_vars[entry['problem__subject']][1]: entry['participant_count']
            for entry in qs_answers
        }
        participants_dict['average'] = max(
            participants_dict[f'subject_{idx}'] for idx, _ in enumerate(self.sub_list)
        )

        scores = {}
        stat_data = {}
        for field, subject_tuple in self.field_vars.items():
            if field in participants_dict.keys():
                participants = participants_dict[field]
                scores[field] = [qs[field] for qs in qs_score]
                student_score = getattr(student.score, field)

                sorted_scores = sorted(scores[field], reverse=True)
                rank = sorted_scores.index(student_score) + 1
                top_10_threshold = max(1, int(participants * 0.1))
                top_20_threshold = max(1, int(participants * 0.2))

                stat_data[field] = {
                    'field': field,
                    'is_confirmed': True,
                    'sub': subject_tuple[0],
                    'subject': subject_tuple[1],
                    'icon': icon_set_new.ICON_SUBJECT[subject_tuple[0]],
                    'rank': rank,
                    'score': student_score,
                    'participants': participants,
                    'max_score': sorted_scores[0],
                    'top_score_10': sorted_scores[top_10_threshold - 1],
                    'top_score_20': sorted_scores[top_20_threshold - 1],
                    'avg_score': sum(scores[field]) / participants,
                }
        return stat_data

    def get_dict_frequency_score(self, student) -> dict:
        score_frequency_list = self.get_score_frequency_list()
        score_counts_list = [round(score / 3, 1) for score in score_frequency_list]
        score_counts_list.sort()

        score_counts = Counter(score_counts_list)
        student_target_score = round(student.score.sum / 3, 1)
        score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

        return {'score_points': dict(score_counts), 'score_colors': score_colors}
