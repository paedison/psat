import dataclasses
import json
from collections import Counter
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.db.models import F, Case, When, Value, BooleanField, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django_htmx.http import reswap

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from scripts.update_prime_result_models import bulk_create_or_update
from .. import models, forms, utils


class ViewConfiguration:
    menu = menu_eng = 'prime'
    menu_kor = '프라임'
    submenu = submenu_eng = 'predict'
    submenu_kor = '모의고사 성적 예측'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_prime_psat_changelist')
    url_list = reverse_lazy('prime:predict-list')


def get_student_dict(user, exam_list):
    students = (
        models.PredictStudent.objects.filter(user=user, psat__in=exam_list)
        .select_related('psat', 'score', 'category').order_by('id')
    )
    return {student.psat: student for student in students}


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
        obj.student = student_dict.get(obj, None)

    context = update_context_data(
        current_time=timezone.now(),
        config=config,
        subjects=subjects,
        icon_subject=icon_set_new.ICON_SUBJECT,
        page_obj=page_obj,
        page_range=page_range
    )
    return render(request, 'a_prime/predict_list.html', context)


def get_detail_context(user, pk: int):
    exam = utils.get_exam(pk)
    exam_vars = ExamVars(exam)
    config = ViewConfiguration()
    config.submenu_kor = f'제{exam.round}회 ' + config.submenu_kor

    student = exam_vars.get_student(user)
    if not student:
        return None

    score_tab = exam_vars.get_score_tab()
    answer_tab = exam_vars.get_answer_tab()

    qs_answer_count = exam_vars.get_qs_answer_count()
    # data_answer_predict = exam_vars.get_data_answer_predict(qs_answer_count)

    qs_student_answer = exam_vars.get_qs_student_answer(student)

    stat_total_all = exam_vars.get_dict_stat_data(student, 'total', False)
    stat_department_all = exam_vars.get_dict_stat_data(student, 'department', False)

    stat_total_filtered = exam_vars.get_dict_stat_data(student, 'total', True)
    stat_department_filtered = exam_vars.get_dict_stat_data(student, 'department', True)

    # frequency_score = exam_vars.get_dict_frequency_score(student)
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
        score_tab=score_tab,
        answer_tab=answer_tab,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 예측 I [All]
        stat_total_all=stat_total_all,
        stat_department_all=stat_department_all,

        # sheet_score: 성적 예측 I [Filtered]
        stat_total_filtered=stat_total_filtered,
        stat_department_filtered=stat_department_filtered,
        #
        # # chart: 성적 분포 차트
        # frequency_score=frequency_score,
        #
        # sheet_answer: 답안 확인
        data_answers=data_answers,
    )
    return context


def detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', 'main')
    context = get_detail_context(request.user, pk)
    if context is None:
        return redirect('prime:predict-list')
    if view_type == 'info_answer':
        return render(request, 'a_prime/snippets/predict_update_info_answer.html', context)
    if view_type == 'score_all':
        return render(request, 'a_prime/snippets/predict_update_sheet_score.html', context)
    return render(request, 'a_prime/predict_detail.html', context)


def modal_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    exam_vars = ExamVars(exam)
    view_type = request.headers.get('View-Type', '')

    form = exam_vars.student_form()
    context = update_context_data(exam=exam, form=form)
    if view_type == 'no_open':
        return render(request, 'a_prime/snippets/modal_predict_no_open.html', context)

    if view_type == 'student_register':
        units = models.choices.unit_choice()
        context = update_context_data(
            context,
            exam_vars=exam_vars,
            units=units,
            header=f'{exam.year}년 대비 제{exam.round}회 프라임 모의고사 수험 정보 입력',
        )
        return render(request, 'a_prime/snippets/modal_predict_student_register.html', context)


def register_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    exam = utils.get_exam(pk)
    if not exam or not exam.is_active:
        return redirect('prime:predict-list')

    exam_vars = ExamVars(exam)
    form = exam_vars.student_form()
    context = update_context_data(exam_vars=exam_vars, exam=exam, form=form)

    if view_type == 'department':
        unit = request.GET.get('unit')
        categories = exam_vars.get_qs_category(unit)
        context = update_context_data(context, categories=categories)
        return render(request, 'a_prime/snippets/department_list.html', context)

    if request.method == 'POST':
        form = exam_vars.student_form(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.user = request.user
            student.psat = exam
            student.save()
            exam_vars.rank_total_model.objects.get_or_create(student=student)
            exam_vars.rank_category_model.objects.get_or_create(student=student)
            exam_vars.score_model.objects.get_or_create(student=student)
            context = update_context_data(context, user_verified=True)

    return render(request, 'a_prime/snippets/modal_predict_student_register.html#student_info', context)


@require_POST
def unregister_view(request: HtmxHttpRequest, pk: int):
    exam = utils.get_exam(pk)
    student = models.PredictStudent.objects.get(psat=exam, user=request.user)
    student.delete()
    return redirect('prime:predict-list')


def answer_input_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    config = ViewConfiguration()
    exam = utils.get_exam(pk)
    if not exam or not exam.is_active:
        return redirect('prime:predict-list')

    config.url_detail = exam.get_predict_detail_url()
    exam_vars = ExamVars(exam)
    student = exam_vars.get_student(request.user)

    field_vars = exam_vars.field_vars.copy()
    field_vars.pop('average')
    sub, subject, field_idx = field_vars[subject_field]

    problem_count = exam_vars.problem_count.copy()
    problem_count.pop('평균')

    answer_data_set = exam_vars.get_input_answer_data_set(request)
    answer_data = answer_data_set[subject_field]

    # answer_submit
    if request.method == 'POST':
        try:
            no = int(request.POST.get('number'))
            ans = int(request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        answer_temporary = {'no': no, 'ans': ans}
        context = update_context_data(subject=subject, answer=answer_temporary, exam=exam)
        response = render(request, 'a_prime/snippets/predict_answer_button.html', context)

        if 1 <= no <= problem_count[sub] and 1 <= ans <= 5:
            answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(answer_data_set), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    answer_student = [
        {'no': no, 'ans': ans} for no, ans in enumerate(answer_data, start=1)
    ]
    context = update_context_data(
        exam=exam, exam_vars=exam_vars, config=config, subject=subject,
        icon_subject=icon_set_new.ICON_SUBJECT[sub],
        student=student, answer_student=answer_student,
        url_answer_confirm=exam.get_predict_answer_confirm_url(subject_field),
    )
    return render(request, 'a_prime/predict_answer_input.html', context)


def answer_confirm_view(request: HtmxHttpRequest, pk: int, subject_field: str):
    exam = utils.get_exam(pk)
    if not exam or not exam.is_active:
        return redirect('prime:predict-list')

    exam_vars = ExamVars(exam)
    student = exam_vars.get_student(request.user)
    sub, subject, field_idx = exam_vars.field_vars[subject_field]

    if request.method == 'POST':
        answer_data_set = exam_vars.get_input_answer_data_set(request)
        answer_data = answer_data_set[subject_field]

        is_confirmed = all(answer_data)
        if is_confirmed:
            exam_vars.create_confirmed_answers(student, sub, answer_data)
            exam_vars.update_answer_counts_after_confirm(sub, answer_data)
            answer_all_confirmed = exam_vars.answer_all_confirmed(student)
            exam_vars.update_statistics_after_confirm(student, subject_field, answer_all_confirmed)

            if answer_all_confirmed and not exam.is_answer_official_opened:
                student.is_filtered = True
                student.save()

        # Load student instance after save
        student = exam_vars.get_student(request.user)
        next_url = exam_vars.get_next_url_for_answer_input(student)

        context = update_context_data(header=f'{subject} 답안 제출', is_confirmed=is_confirmed, next_url=next_url)
        return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)

    context = update_context_data(
        url_answer_confirm=exam.get_predict_answer_confirm_url(subject_field),
        header=f'{subject} 답안을 제출하시겠습니까?', verifying=True)
    return render(request, 'a_predict/snippets/modal_answer_confirmed.html', context)


@dataclasses.dataclass
class ExamVars:
    exam: models.Psat

    exam_model = models.Psat
    problem_model = models.Problem
    category_model = models.Category

    statistics_model = models.PredictStatistics
    answer_count_model = models.PredictAnswerCount

    student_model = models.PredictStudent
    answer_model = models.PredictAnswer
    score_model = models.PredictScore
    rank_total_model = models.PredictRankTotal
    rank_category_model = models.PredictRankCategory

    student_form = forms.PrimePredictStudentForm

    current_time = datetime.now(pytz.UTC)

    sub_list = ['헌법', '언어', '자료', '상황']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    problem_count = {'헌법': 25, '언어': 40, '자료': 40, '상황': 40, '평균': 120}
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
    final_field = 'average'

    # Template constants
    score_template_table_1 = 'a_prime/snippets/predict_detail_sheet_score_table_1.html'
    score_template_table_2 = 'a_prime/snippets/predict_detail_sheet_score_table_2.html'

    def get_student(self, user) -> models.PredictStudent:
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

        student = (
            self.student_model.objects.filter(user=user, psat=self.exam)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .prefetch_related('answers')
            .annotate(department=F('category__department'), **annotate_dict)
            .order_by('id').last()
        )

        qs_answer_count = (
            student.answers
            .values(subject=F('problem__subject'))
            .annotate(answer_count=Count('id'))
        )
        average_answer_count = 0
        for q in qs_answer_count:
            student.answer_count[q['subject']] = q['answer_count']
            if q['subject'] != '헌법':
                average_answer_count += q['answer_count']
        student.answer_count['평균'] = average_answer_count

        return student

    def get_qs_category(self, unit=None):
        if unit:
            return self.category_model.objects.filter(unit=unit).order_by('order')
        return self.category_model.objects.order_by('order')

    def get_qs_student_answer(self, student):
        return models.PredictAnswer.objects.filter(
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

    def get_qs_answer_count(self):
        return self.answer_count_model.objects.filter(problem__psat=self.exam).annotate(
            no=F('problem__number'), sub=F('problem__subject')).order_by('sub', 'no')

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

    def get_qs_answers(self, student: models.PredictStudent, stat_type: str, is_filtered: bool):
        qs_answers = (
            self.answer_model.objects.filter(problem__psat=self.exam).values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        if stat_type == 'department':
            qs_answers = qs_answers.filter(student__category__department=student.category.department)
        if is_filtered:
            qs_answers = qs_answers.filter(student__is_filtered=True)
        return qs_answers

    def get_qs_score(self, student: models.PredictStudent, stat_type: str, is_filtered: bool):
        qs_score = self.score_model.objects.filter(student__psat=self.exam)
        if stat_type == 'department':
            qs_score = qs_score.filter(student__category__department=student.category.department)
        if is_filtered:
            qs_score = qs_score.filter(student__is_filtered=True)
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
            {
                'id': str(idx),
                'title': sub,
                'subject': self.subject_vars[sub][0],
                'field': self.subject_vars[sub][1],
                'icon': icon_set_new.ICON_SUBJECT[sub],
                'url_answer_input': self.exam.get_predict_answer_input_url(
                    self.subject_vars[sub][1]) if sub != '평균' else '',
            } for idx, sub in enumerate(self.sub_list)
        ]

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

    def get_data_answers(self, qs_student_answer):
        data_answers = [[] for _ in self.sub_list]

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
            if line.rate_correct_top is not None and line.rate_correct_low is not None:
                line.rate_gap = line.rate_correct_top - line.rate_correct_low
            else:
                line.rate_gap = 0

            line.rate_selection = line.problem.result_answer_count.get_answer_rate(ans_student)
            line.rate_selection_top = line.problem.result_answer_count_top_rank.get_answer_rate(ans_student)
            line.rate_selection_mid = line.problem.result_answer_count_mid_rank.get_answer_rate(ans_student)
            line.rate_selection_low = line.problem.result_answer_count_low_rank.get_answer_rate(ans_student)

            data_answers[idx].append(line)
        return data_answers

    def get_dict_stat_data(self, student: models.PredictStudent, stat_type: str, is_filtered: bool):
        qs_answers = self.get_qs_answers(student, stat_type, is_filtered)
        qs_score = self.get_qs_score(student, stat_type, is_filtered)

        stat_data = []
        for sub, (subject, fld) in self.subject_vars.items():
            url_answer_input = self.exam.get_predict_answer_input_url(fld) if sub != '평균' else ''
            stat_data.append({
                'field': fld,
                'sub': sub,
                'subject': subject,
                'icon': icon_set_new.ICON_SUBJECT[sub],

                'participants': 0,
                'is_confirmed': False,
                'url_answer_input': url_answer_input,

                'score_real': 0,
                'score_predict': 0,
                'problem_count': self.problem_count.get(sub),
                'answer_count': student.answer_count.get(sub, 0),

                'rank': 0,
                'score': 0,
                'max_score': 0,
                'top_score_10': 0,
                'top_score_20': 0,
                'avg_score': 0,
            })

        participants_dict = {
            self.subject_vars[entry['problem__subject']][1]: entry['participant_count']
            for entry in qs_answers
        }
        max_participants = max(
            participants_dict.get(f'subject_{idx}', 0) for idx, _ in enumerate(self.sub_list)
        )
        if max_participants:
            participants_dict['average'] = max_participants

        scores = {}
        for stat in stat_data:
            fld = stat['field']
            if fld in participants_dict.keys():
                participants = participants_dict[fld]
                stat.update({
                    'participants': participants,
                    'is_confirmed': True,
                })
                if self.exam.is_answer_official_opened:
                    scores[fld] = [qs[fld] for qs in qs_score]
                    student_score = getattr(student.score, fld)
                    sorted_scores = sorted(scores[fld], reverse=True)
                    rank = sorted_scores.index(student_score) + 1
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    avg_score = sum(scores[fld]) / participants if any(scores[fld]) else 0
                    stat.update({
                        'rank': rank,
                        'score': student_score,
                        'max_score': sorted_scores[0],
                        'top_score_10': sorted_scores[top_10_threshold - 1],
                        'top_score_20': sorted_scores[top_20_threshold - 1],
                        'avg_score': avg_score,
                    })
        return stat_data

    def get_dict_frequency_score(self, student) -> dict:
        score_frequency_list = self.get_score_frequency_list()
        score_counts_list = [round(score / 3, 1) for score in score_frequency_list]
        score_counts_list.sort()

        score_counts = Counter(score_counts_list)
        student_target_score = round(student.score.sum / 3, 1)
        score_colors = ['blue' if score == student_target_score else 'white' for score in score_counts.keys()]

        return {'score_points': dict(score_counts), 'score_colors': score_colors}

    def get_input_answer_data_set(self, request):
        problem_count = self.problem_count.copy()
        problem_count.pop('평균')

        empty_answer_data = {
            self.subject_vars[sub][1]: [0 for _ in range(cnt)] for sub, cnt in problem_count.items()
        }
        answer_data_set_cookie = request.COOKIES.get('answer_data_set', '{}')
        answer_data_set = json.loads(answer_data_set_cookie) or empty_answer_data
        return answer_data_set

    def get_next_url_for_answer_input(self, student):
        for sub in self.sub_list:
            subject_field = self.subject_vars[sub][1]
            if student.answer_count[sub] == 0:
                return self.exam.get_predict_answer_input_url(subject_field)
        return self.exam.get_predict_detail_url()

    def create_confirmed_answers(self, student, sub, answer_data):
        list_create = []
        for no, ans in enumerate(answer_data, start=1):
            problem = self.problem_model.objects.get(psat=self.exam, subject=sub, number=no)
            list_create.append(self.answer_model(student=student, problem=problem, answer=ans))
        bulk_create_or_update(self.answer_model, list_create, [], [])

    def update_answer_counts_after_confirm(self, sub, answer_data):
        qs_answer_count = self.get_qs_answer_count().filter(sub=sub)
        for answer_count in qs_answer_count:
            ans_student = answer_data[answer_count.problem.number - 1]
            setattr(answer_count, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
            setattr(answer_count, f'count_sum', F(f'count_sum') + 1)
            if not self.exam.is_answer_official_opened:
                setattr(answer_count, f'filtered_count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(answer_count, f'filtered_count_sum', F(f'count_sum') + 1)
            answer_count.save()

    def answer_all_confirmed(self, student) -> bool:
        answer_student_counts = self.answer_model.objects.filter(student=student).count()
        problem_count = self.problem_count.copy()
        problem_count.pop('평균')
        return answer_student_counts == sum(problem_count.values())

    def update_statistics_after_confirm(self, student, subject_field, answer_all_confirmed):
        def get_statistics_and_edit_participants(department: str):
            stat = get_object_or_404(self.statistics_model, psat=self.exam, department=department)

            # Update participants for each subject [All, Filtered]
            getattr(stat, subject_field)['participants'] += 1
            if not self.exam.is_answer_official_opened:
                getattr(stat, f'filtered_{subject_field}')['participants'] += 1

            # Update participants for average [All, Filtered]
            if answer_all_confirmed:
                stat.average['participants'] += 1
                if not self.exam.is_answer_official_opened:
                    stat.filtered_average['participants'] += 1
                    student.is_filtered = True
                    student.save()
            stat.save()

        get_statistics_and_edit_participants('전체')
        get_statistics_and_edit_participants(student.department)
