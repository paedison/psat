import dataclasses
from collections import Counter

from django.core.paginator import Paginator
from django.db.models import F, Case, When, Value, BooleanField, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, forms


class ViewConfiguration:
    menu = menu_eng = 'prime_leet'
    menu_kor = '프라임LEET'
    submenu = submenu_eng = 'score'
    submenu_kor = '모의고사 성적 확인'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_leet_leet_changelist')
    url_list = reverse_lazy('prime_leet:score-list')


def get_student_dict(user, exam_list):
    annotate_dict = {}
    field_dict = {0: 'subject_0', 1: 'subject_1', 'sum': 'sum'}
    for key, fld in field_dict.items():
        annotate_dict[f'raw_score_{key}'] = F(f'score__raw_{fld}')
        annotate_dict[f'score_{key}'] = F(f'score__{fld}')
    students = (
        models.ResultStudent.objects.filter(registries__user=user, leet__in=exam_list)
        .select_related('leet', 'score', 'rank').order_by('id').annotate(**annotate_dict)
    )
    return {student.leet: student for student in students}


def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    exam_list = models.Leet.objects.filter(year=2025)

    subjects = [
        ('총점', 'sum'),
        ('언어이해', 'subject_0'),
        ('추리논증', 'subject_1'),
    ]

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    student_dict = get_student_dict(request.user, exam_list)
    for obj in page_obj:
        obj.student = student_dict.get(obj, None)

    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        subjects=subjects,
        icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj,
        page_range=page_range
    )
    return render(request, 'a_prime_leet/score_list.html', context)


def get_detail_context(user, pk: int):
    exam = get_object_or_404(models.Leet, pk=pk)
    exam_vars = ExamVars(exam)
    config = ViewConfiguration()
    config.submenu_kor = f'제{exam.round}회 ' + config.submenu_kor

    student = exam_vars.get_student(user)
    if not student:
        return redirect('prime_leet:score-list')

    stat_data = exam_vars.get_dict_stat_data(student)
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

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_data=stat_data,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answers=data_answers,
    )
    return context


def detail_view(request: HtmxHttpRequest, pk: int):
    context = get_detail_context(request.user, pk)
    return render(request, 'a_prime_leet/score_detail.html', context)


def print_view(request: HtmxHttpRequest, pk: int):
    context = get_detail_context(request.user, pk)
    return render(request, 'a_prime_leet/score_print.html', context)


def modal_view(request: HtmxHttpRequest, pk: int):
    exam = models.Leet.objects.get(pk=pk)
    exam_vars = ExamVars(exam)

    hx_modal = request.headers.get('View-Modal', '')
    is_no_open = hx_modal == 'no_open'
    is_student_register = hx_modal == 'student_register'

    context = update_context_data(exam=exam)
    if is_no_open:
        return render(request, 'a_prime_leet/snippets/modal_no_open.html', context)

    if is_student_register:
        context = update_context_data(
            context,
            exam_vars=exam_vars,
            header=f'{exam.year}년 대비 제{exam.round}회 프라임 LEET 모의고사 수험 정보 입력',
        )
        return render(request, 'a_prime_leet/snippets/modal_student_register.html', context)


@require_POST
def register_view(request: HtmxHttpRequest, pk: int):
    exam = models.Leet.objects.get(pk=pk)
    exam_vars = ExamVars(exam)

    form = exam_vars.student_form(data=request.POST, files=request.FILES)
    context = update_context_data(exam_vars=exam_vars, exam=exam, form=form)
    if form.is_valid():
        serial = form.cleaned_data['serial']
        name = form.cleaned_data['name']
        password = form.cleaned_data['password']
        try:
            target_student = exam_vars.student_model.objects.get(
                leet=exam, serial=serial, name=name, password=password)
            registered_student, _ = models.ResultRegistry.objects.get_or_create(
                user=request.user, student=target_student)
            context = update_context_data(context, user_verified=True)
        except exam_vars.student_model.DoesNotExist:
            context = update_context_data(context, no_student=True)

    return render(request, 'a_prime_leet/snippets/modal_student_register.html#student_info', context)


@require_POST
def unregister_view(request: HtmxHttpRequest, pk: int):
    leet = models.Leet.objects.get(pk=pk)
    student = models.ResultRegistry.objects.get(student__leet=leet, user=request.user)
    student.delete()
    return redirect('prime_leet:score-list')


@dataclasses.dataclass
class ExamVars:
    exam: models.Leet

    exam_model = models.Leet
    problem_model = models.Problem
    student_model = models.ResultStudent
    answer_model = models.ResultAnswer
    answer_count_model = models.ResultAnswerCount
    score_model = models.ResultScore
    rank_model = models.ResultRank
    student_form = forms.PrimeLeetStudentForm

    sub_list = ['언어', '추리']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    problem_count = {'언어': 30, '추리': 40}
    subject_vars = {
        '언어': ('언어이해', 'subject_0'),
        '추리': ('추리논증', 'subject_1'),
        '총점': ('총점', 'sum'),
    }
    field_vars = {
        'subject_0': ('언어', '언어이해', 0),
        'subject_1': ('추리', '추리논증', 1),
        'sum': ('총점', '총점', 2),
    }

    def get_student(self, user):
        annotate_dict = {
            'score_sum': F('score__sum'),
            'rank_num': F(f'rank__participants'),
        }
        field_dict = {0: 'subject_0', 1: 'subject_1', 2: 'sum'}
        for key, fld in field_dict.items():
            annotate_dict[f'score_{key}'] = F(f'score__{fld}')
            annotate_dict[f'rank_{key}'] = F(f'rank__{fld}')

        return (
            self.student_model.objects.filter(registries__user=user, leet=self.exam)
            .select_related('leet', 'score', 'rank')
            .annotate(**annotate_dict).order_by('id').last()
        )

    def get_qs_student_answer(self, student):
        return models.ResultAnswer.objects.filter(
            problem__leet=self.exam, student=student).annotate(
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
            self.problem_model.objects.filter(leet=self.exam)
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

    def get_qs_answers(self):
        qs_answers = (
            self.answer_model.objects.filter(problem__leet=self.exam).values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        return qs_answers

    def get_qs_score(self):
        qs_score = self.score_model.objects.filter(student__leet=self.exam)
        return qs_score.values()

    def get_score_frequency_list(self) -> list:
        return self.student_model.objects.filter(leet=self.exam).values_list('score__sum', flat=True)

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

            line.rate_selection = line.problem.result_answer_count.get_answer_rate(ans_student)
            line.rate_selection_top = line.problem.result_answer_count_top_rank.get_answer_rate(ans_student)
            line.rate_selection_mid = line.problem.result_answer_count_mid_rank.get_answer_rate(ans_student)
            line.rate_selection_low = line.problem.result_answer_count_low_rank.get_answer_rate(ans_student)

            data_answers[idx].append(line)
        return data_answers

    def get_dict_stat_data(self, student: models.ResultStudent) -> dict:
        qs_answers = self.get_qs_answers()
        qs_score = self.get_qs_score()

        participants_dict = {
            self.subject_vars[entry['problem__subject']][1]: entry['participant_count']
            for entry in qs_answers
        }
        participants_dict['sum'] = max(
            participants_dict[f'subject_{idx}'] for idx, _ in enumerate(self.sub_list)
        )

        raw_scores = {}
        scores = {}
        stat_data = {}
        for field, subject_tuple in self.field_vars.items():
            if field in participants_dict.keys():
                participants = participants_dict[field]
                raw_scores[field] = [qs[f'raw_{field}'] for qs in qs_score]
                scores[field] = [qs[field] for qs in qs_score]
                student_raw_score = getattr(student.score, f'raw_{field}')
                student_score = getattr(student.score, field)

                sorted_raw_scores = sorted(raw_scores[field], reverse=True)
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
                    'raw_score': student_raw_score,
                    'score': student_score,
                    'participants': participants,
                    'max_raw_score': sorted_raw_scores[0],
                    'max_score': sorted_scores[0],
                    'top_raw_score_10': sorted_raw_scores[top_10_threshold - 1],
                    'top_score_10': sorted_scores[top_10_threshold - 1],
                    'top_raw_score_20': sorted_raw_scores[top_20_threshold - 1],
                    'top_score_20': sorted_scores[top_20_threshold - 1],
                    'avg_raw_score': sum(raw_scores[field]) / participants,
                    'avg_score': sum(scores[field]) / participants,
                }
        return stat_data

    def get_dict_frequency_score(self, student) -> dict:
        score_frequency_list = self.get_score_frequency_list()
        score_counts_list = [round(score, 1) for score in score_frequency_list]
        score_counts_list.sort()

        score_counts = Counter(score_counts_list)
        student_target_score = round(student.score.sum, 1)
        score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

        return {'score_points': dict(score_counts), 'score_colors': score_colors}
