import dataclasses
import itertools
import traceback
from collections import defaultdict

import django.db.utils
import pandas as pd
from django.db import transaction
from django.db.models import Count, Window, F
from django.db.models.functions import Rank
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django_htmx.http import replace_url

from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms, filters


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-list')
    url_psat_create = reverse_lazy('psat:admin-psat-create')
    url_problem_update = reverse_lazy('psat:admin-problem-update')

    url_predict_create = reverse_lazy('psat:admin-predict-create')


@admin_required
def list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    page_number = request.GET.get('page', '1')

    sub_title = utils.get_sub_title_by_psat(exam_year, exam_exam, '', end_string='PSAT')
    filterset = filters.PsatFilter(data=request.GET, request=request)

    page_obj, page_range = utils.get_paginator_data(filterset.qs, page_number)
    for psat in page_obj:
        psat.updated_problem_count = sum(1 for problem in psat.problems.all() if problem.question and problem.data)
        psat.image_problem_count = sum(1 for problem in psat.problems.all() if problem.has_image)

    predict_exam_list = models.PredictPsat.objects.all()
    predict_page_obj, predict_page_range = utils.get_paginator_data(predict_exam_list, page_number)

    context = update_context_data(
        config=config, sub_title=sub_title, psat_form=filterset.form,
        page_obj=page_obj, page_range=page_range,
        predict_page_obj=predict_page_obj, predict_page_range=predict_page_range,
    )
    if view_type == 'exam_list':
        template_name = 'a_psat/admin_list.html#exam_list'
        return render(request, template_name, context)

    return render(request, 'a_psat/admin_list.html', context)


@admin_required
def psat_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.PsatForm(request.POST, request.FILES)
        if form.is_valid():
            psat = form.save(commit=False)
            exam = form.cleaned_data['exam']
            exam_order = {'행시': 1, '입시':2, '칠급': 3}
            psat.order = exam_order.get(exam)
            psat.save()
            create_list = []
            if exam in ['행시', '입시']:
                append_create_list(create_list, psat, 40, *['언어', '자료', '상황'])
                append_create_list(create_list, psat, 25, *['헌법'])
            elif exam in ['칠급']:
                append_create_list(create_list, psat, 25, *['언어', '자료', '상황'])

            messages = {}
            if create_list:
                try:
                    with transaction.atomic():
                        if create_list:
                            models.Problem.objects.bulk_create(create_list)
                            messages['create'] = f'Successfully updated {len(create_list)} Problem instances.'
                        else:
                            messages['error'] = f'No changes were made to Problem instances.'
                except django.db.utils.IntegrityError:
                    traceback_message = traceback.format_exc()
                    print(traceback_message)
                    messages['error'] = 'An error occurred during the transaction.'

            for message in messages.values():
                if message:
                    print(message)

            response = redirect('psat:admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_psat/admin_exam_create.html', context)

    form = forms.PsatForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_exam_create.html', context)


def append_create_list(create_list: list, psat: models.Psat, problem_count: int, *subject_list):
    for subject in subject_list:
        for number in range(1, problem_count + 1):
            problem_info = {'psat': psat, 'subject': subject, 'number': number}
            try:
                models.Problem.objects.get(**problem_info)
            except models.Problem.DoesNotExist:
                create_list.append(models.Problem(**problem_info))


@admin_required
def psat_active_view(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        form = forms.PsatActiveForm(request.POST)
        if form.is_valid():
            psat = get_object_or_404(models.Psat, pk=pk)
            is_active = form.cleaned_data['is_active']
            psat.is_active = is_active
            psat.save()
    return HttpResponse('')


@admin_required
def problem_update_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.ProblemUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            psat = get_object_or_404(models.Psat, year=year, exam=exam)

            update_file = request.FILES['update_file']
            df = pd.read_excel(update_file, header=0, index_col=0)

            answer_symbol = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
            keys = list(answer_symbol.keys())
            combinations = []
            for i in range(1, 6):
                combinations.extend(itertools.combinations(keys, i))

            replace_dict = {}
            for combination in combinations:
                key = ''.join(combination)
                value = int(''.join(str(answer_symbol[k]) for k in combination))
                replace_dict[key] = value

            df['answer'].replace(to_replace=replace_dict, inplace=True)
            df = df.infer_objects(copy=False)

            for index, row in df.iterrows():
                problem = models.Problem.objects.get(psat=psat, subject=row['subject'], number=row['number'])
                problem.paper_type = row['paper_type']
                problem.answer = row['answer']
                problem.question = row['question']
                problem.data = row['data']
                problem.save()

            response = redirect('psat:admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_psat/admin_problem_update.html', context)

    form = forms.ProblemUpdateForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_problem_update.html', context)


@admin_required
def detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    subject = request.GET.get('subject', '')
    student_name = request.GET.get('student_name', '')

    psat = utils.get_psat(pk)
    problems = models.Problem.objects.select_related(
        'psat').filter(psat=psat).annotate(no=F('number'), ans=F('answer'))
    page_obj, page_range = utils.get_paginator_data(problems, page_number)

    subject_list = ['헌법', '언어', '자료', '상황']
    if psat.exam in ['칠급', '칠예', '민경']:
        subject_list.remove('헌법')

    queryset_dict = defaultdict(list)
    for problem in problems.order_by('id'):
        queryset_dict[problem.subject].append(problem)
    answer_official_list = [queryset_dict[sub] for sub in subject_list]

    context = update_context_data(
        config=config, psat=psat, subjects=subject_list,
        answer_official_list=answer_official_list,
        page_obj=page_obj, page_range=page_range,
    )

    predict_psat = utils.get_predict_psat(psat)
    if predict_psat:
        exam_vars = ExamVars(predict_psat)
        answer_tab = exam_vars.get_answer_tab()

        config.url_admin_predict_update = reverse_lazy('psat:admin-predict-update', args=[pk])

        context = update_context_data(
            context, predict_psat=predict_psat, answer_tab=answer_tab,
            icon_nav=icon_set_new.ICON_NAV, icon_search=icon_set_new.ICON_SEARCH,
        )
        data_statistics = exam_vars.get_qs_statistics()
        student_list = exam_vars.get_student_list()
        qs_answer_count = exam_vars.get_qs_answer_count(subject)

        if view_type == 'statistics_list':
            statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
            context = update_context_data(
                context, statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range)
            return render(request, 'a_psat/snippets/admin_detail_predict_statistics.html', context)
        if view_type == 'catalog_list':
            catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
            context = update_context_data(
                context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'student_search':
            searched_student = student_list.filter(name=student_name)
            catalog_page_obj, catalog_page_range = utils.get_paginator_data(searched_student, page_number)
            context = update_context_data(
                context, catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range)
            return render(request, 'a_psat/snippets/admin_detail_predict_catalog.html', context)
        if view_type == 'answer_list':
            subject_idx = exam_vars.subject_vars[subject][2]
            answers_page_obj_group, answers_page_range_group = (
                exam_vars.get_answer_page_data(qs_answer_count, page_number, 10))
            context = update_context_data(
                context,
                tab=answer_tab[subject_idx],
                answers=answers_page_obj_group[subject],
                answers_page_range=answers_page_range_group[subject],
            )
            return render(request, 'a_psat/snippets/admin_detail_predict_answer_analysis.html', context)

        statistics_page_obj, statistics_page_range = utils.get_paginator_data(data_statistics, page_number)
        catalog_page_obj, catalog_page_range = utils.get_paginator_data(student_list, page_number)
        answers_page_obj_group, answers_page_range_group = (
            exam_vars.get_answer_page_data(qs_answer_count, page_number, 10))

        context = update_context_data(
            context,
            statistics_page_obj=statistics_page_obj, statistics_page_range=statistics_page_range,
            catalog_page_obj=catalog_page_obj, catalog_page_range=catalog_page_range,
            answers_page_obj_group=answers_page_obj_group, answers_page_range_group=answers_page_range_group,
        )
    return render(request, 'a_psat/admin_detail.html', context)


@admin_required
def predict_create_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    if request.method == 'POST':
        form = forms.PredictPsatForm(request.POST, request.FILES)
        if form.is_valid():
            year = form.cleaned_data['year']
            exam = form.cleaned_data['exam']
            original_psat = models.Psat.objects.get(year=year, exam=exam)

            new_predict_psat, _ = models.PredictPsat.objects.get_or_create(psat=original_psat)
            new_predict_psat.is_active = True
            new_predict_psat.page_opened_at = form.cleaned_data['page_opened_at']
            new_predict_psat.exam_started_at = form.cleaned_data['exam_started_at']
            new_predict_psat.exam_finished_at = form.cleaned_data['exam_finished_at']
            new_predict_psat.answer_predict_opened_at = form.cleaned_data['answer_predict_opened_at']
            new_predict_psat.answer_official_opened_at = form.cleaned_data['answer_official_opened_at']
            new_predict_psat.predict_closed_at = form.cleaned_data['predict_closed_at']
            new_predict_psat.save()

            exam_vars = ExamVars(new_predict_psat)
            problems = models.Problem.objects.filter(psat=original_psat).order_by('id')
            exam_vars.create_default_answer_counts(problems)
            exam_vars.create_default_statistics()

            response = redirect('psat:admin-list')
            return replace_url(response, config.url_list)
        else:
            context = update_context_data(config=config, form=form)
            return render(request, 'a_psat/admin_predict_create.html', context)

    form = forms.PredictPsatForm()
    context = update_context_data(config=config, form=form)
    return render(request, 'a_psat/admin_predict_create.html', context)


@admin_required
def predict_update_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')

    exam = get_object_or_404(models.Psat, pk=pk)
    exam_vars = ExamVars(exam.predict_psat)

    context = {}
    next_url = exam.get_admin_detail_url()
    qs_student = exam_vars.get_qs_student()

    if view_type == 'answer_official':
        is_updated, message = exam_vars.update_problem_model_for_answer_official(request)
        context = update_context_data(
            header='정답 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'score':
        is_updated, message = exam_vars.update_scores(qs_student)
        context = update_context_data(
            header='점수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'rank':
        is_updated, message = exam_vars.update_ranks(qs_student)
        context = update_context_data(
            header='등수 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'statistics':
        data_statistics = exam_vars.get_data_statistics()
        is_updated, message = exam_vars.update_statistics_model(data_statistics)
        context = update_context_data(
            header='통계 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    if view_type == 'answer_count':
        is_updated, message = exam_vars.update_answer_counts()
        context = update_context_data(
            header='문항분석표 업데이트', next_url=next_url, is_updated=is_updated, message=message)

    return render(request, 'a_psat/snippets/admin_modal_predict_update.html', context)


@dataclasses.dataclass
class ExamVars:
    exam: models.PredictPsat

    exam_model = models.PredictPsat
    problem_model = models.Problem
    category_model = models.PredictCategory

    # Predict Models
    student_model = models.PredictStudent
    answer_model = models.PredictAnswer
    score_model = models.PredictScore
    rank_total_model = models.PredictRankTotal
    rank_category_model = models.PredictRankCategory
    statistics_model = models.PredictStatistics
    answer_count_model = models.PredictAnswerCount
    answer_count_top_model = models.PredictAnswerCountTopRank
    answer_count_mid_model = models.PredictAnswerCountMidRank
    answer_count_low_model = models.PredictAnswerCountLowRank

    upload_file_form = forms.UploadFileForm

    sub_list = ['헌법', '언어', '자료', '상황']
    subject_list = [models.choices.subject_choice()[key] for key in sub_list]
    problem_count = {'헌법': 25, '언어': 40, '자료': 40, '상황': 40}
    subject_vars = {
        '헌법': ('헌법', 'subject_0', 0),
        '언어': ('언어논리', 'subject_1', 1),
        '자료': ('자료해석', 'subject_2', 2),
        '상황': ('상황판단', 'subject_3', 3),
        '평균': ('PSAT 평균', 'average', 4),
    }
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }

    # Template constants
    score_template_table_1 = 'a_psat/snippets/detail_sheet_score_table_1.html'
    score_template_table_2 = 'a_psat/snippets/detail_sheet_score_table_2.html'

    def get_qs_student(self):
        return self.student_model.objects.filter(psat=self.exam.psat).order_by('id')

    def get_qs_answers(self, student: models.PredictStudent, stat_type: str):
        qs_answers = (
            self.answer_model.objects.filter(problem__psat=self.exam.psat).values('problem__subject')
            .annotate(participant_count=Count('student_id', distinct=True))
        )
        if stat_type == 'department':
            qs_answers = qs_answers.filter(student__category__department=student.category.department)
        return qs_answers

    def get_student_list(self):
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
            self.student_model.objects.filter(psat=self.exam.psat)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .order_by('psat__year', 'psat__order', 'rank_total__average')
            .annotate(department=F('category__department'), **annotate_dict)
        )

    def get_qs_answer_count(self, subject=None):
        annotate_dict = {
            'subject': F('problem__subject'),
            'number': F('problem__number'),
            'ans_predict': F(f'problem__predict_answer_count__answer_predict'),
            'ans_official': F('problem__answer'),
        }
        field_list = ['count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_sum']
        for fld in field_list:
            annotate_dict[f'{fld}_all'] = F(f'{fld}')
            annotate_dict[f'{fld}_top'] = F(f'problem__predict_answer_count_top_rank__{fld}')
            annotate_dict[f'{fld}_mid'] = F(f'problem__predict_answer_count_mid_rank__{fld}')
            annotate_dict[f'{fld}_low'] = F(f'problem__predict_answer_count_low_rank__{fld}')
        qs_answer_count = (
            self.answer_count_model.objects.filter(problem__psat=self.exam.psat)
            .order_by('problem__subject', 'problem__number').annotate(**annotate_dict)
            .select_related(
                f'problem',
                f'problem__predict_answer_count',
                f'problem__predict_answer_count_top_rank',
                f'problem__predict_answer_count_mid_rank',
                f'problem__predict_answer_count_low_rank',
            )
        )
        if subject:
            qs_answer_count = qs_answer_count.filter(subject=subject)
        return qs_answer_count

    def get_qs_statistics(self):
        return self.statistics_model.objects.filter(psat=self.exam.psat).order_by('id')

    def get_qs_score(self, student: models.PredictStudent, stat_type: str):
        qs_score = self.score_model.objects.filter(student__psat=self.exam.psat)
        if stat_type == 'department':
            qs_score = qs_score.filter(student__category__department=student.category.department)
        return qs_score.values()

    def get_score_frequency_list(self) -> list:
        return self.student_model.objects.filter(psat=self.exam.psat).values_list('score__sum', flat=True)

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

    @staticmethod
    def get_answer_rate(answer_count, ans: int, count_sum: int, answer_official_list=None):
        if answer_official_list:
            return sum(
                getattr(answer_count, f'count_{ans_official}') for ans_official in answer_official_list
            ) * 100 / count_sum
        return getattr(answer_count, f'count_{ans}') * 100 / count_sum

    def get_answer_page_data(self, qs_answer_count, page_number, per_page=10):
        qs_answer_count_group, answers_page_obj_group, answers_page_range_group = {}, {}, {}

        for entry in qs_answer_count:
            if entry.subject not in qs_answer_count_group:
                qs_answer_count_group[entry.subject] = []
            qs_answer_count_group[entry.subject].append(entry)

        for subject, qs_answer_count in qs_answer_count_group.items():
            if subject not in answers_page_obj_group:
                answers_page_obj_group[subject] = []
                answers_page_range_group[subject] = []
            data_answers = self.get_data_answers(qs_answer_count)
            answers_page_obj_group[subject], answers_page_range_group[subject] = utils.get_paginator_data(
                data_answers, page_number, per_page)

        return answers_page_obj_group, answers_page_range_group

    def get_data_answers(self, qs_answer_count):
        for entry in qs_answer_count:
            sub = entry.subject
            field = self.subject_vars[sub][1]
            ans_official = entry.ans_official

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            entry.no = entry.number
            entry.ans_official = ans_official
            entry.ans_official_circle = entry.problem.get_answer_display
            entry.ans_list = answer_official_list
            entry.field = field

            entry.rate_correct = entry.get_answer_rate(ans_official)
            entry.rate_correct_top = entry.problem.predict_answer_count_top_rank.get_answer_rate(ans_official)
            entry.rate_correct_mid = entry.problem.predict_answer_count_mid_rank.get_answer_rate(ans_official)
            entry.rate_correct_low = entry.problem.predict_answer_count_low_rank.get_answer_rate(ans_official)
            try:
                entry.rate_gap = entry.rate_correct_top - entry.rate_correct_low
            except TypeError:
                entry.rate_gap = None

        return qs_answer_count

    def update_problem_model_for_answer_official(self, request) -> tuple:
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문제 정답을 업데이트했습니다.',
            False: '기존 정답 데이터와 일치합니다.',
        }
        list_update = []
        list_create = []

        form = self.upload_file_form(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            df = pd.read_excel(uploaded_file, sheet_name='정답', header=0, index_col=0)
            df = df.infer_objects(copy=False)
            df.fillna(value=0, inplace=True)

            for subject, rows in df.items():
                for number, answer in rows.items():
                    if answer:
                        try:
                            problem = self.problem_model.objects.get(
                                psat=self.exam.psat, subject=subject[0:2], number=number)
                            if problem.answer != answer:
                                problem.answer = answer
                                list_update.append(problem)
                        except self.problem_model.DoesNotExist:
                            problem = self.problem_model(
                                psat=self.exam.psat, subject=subject, number=number, answer=answer)
                            list_create.append(problem)
                        except ValueError as error:
                            print(error)
            update_fields = ['answer']
            is_updated = bulk_create_or_update(self.problem_model, list_create, list_update, update_fields)
        else:
            is_updated = None
            print(form)
        return is_updated, message_dict[is_updated]

    def update_score_model(self, qs_student, model_dict):
        answer_model = model_dict['answer']
        score_model = model_dict['score']

        list_update = []
        list_create = []

        for student in qs_student:
            original_score_instance, _ = score_model.objects.get_or_create(student=student)

            score_list = []
            fields_not_match = []
            for idx, sub in enumerate(self.sub_list):
                problem_count = 25 if sub == '헌법' else 40
                correct_count = 0

                qs_answer = (
                    answer_model.objects.filter(student=student, problem__subject=sub)
                    .annotate(answer_correct=F('problem__answer'), answer_student=F('answer'))
                )
                for entry in qs_answer:
                    answer_correct_list = [int(digit) for digit in str(entry.answer_correct)]
                    correct_count += 1 if entry.answer_student in answer_correct_list else 0

                score = correct_count * 100 / problem_count
                score_list.append(score)
                fields_not_match.append(getattr(original_score_instance, f'subject_{idx}') != score)

            score_sum = sum(score_list[1:])
            average = round(score_sum / 3, 1)

            fields_not_match.append(original_score_instance.sum != score_sum)
            fields_not_match.append(original_score_instance.average != average)

            if any(fields_not_match):
                for idx, score in enumerate(score_list):
                    setattr(original_score_instance, f'subject_{idx}', score)
                original_score_instance.sum = score_sum
                original_score_instance.average = average
                list_update.append(original_score_instance)

        update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'sum', 'average']
        return bulk_create_or_update(score_model, list_create, list_update, update_fields)

    def update_scores(self, qs_student):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '점수를 업데이트했습니다.',
            False: '기존 점수와 일치합니다.',
        }

        model_dict = {
            'answer': self.answer_model,
            'score': self.score_model,
        }
        is_updated_list = [self.update_score_model(qs_student, model_dict)]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def update_rank_model(self, qs_student, model_dict, stat_type='total'):
        rank_model = model_dict[stat_type]

        list_create = []
        list_update = []
        subject_count = len(self.sub_list)

        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        annotate_dict = {f'rank_{idx}': rank_func(f'score__subject_{idx}') for idx in range(subject_count)}
        annotate_dict['rank_average'] = rank_func('score__average')

        participants = qs_student.count()
        for student in qs_student:
            rank_list = qs_student.annotate(**annotate_dict)
            if stat_type == 'department':
                rank_list = rank_list.filter(category=student.category)
            target, _ = rank_model.objects.get_or_create(student=student)

            fields_not_match = [target.participants != participants]
            for row in rank_list:
                if row.id == student.id:
                    for idx in range(subject_count):
                        fields_not_match.append(
                            getattr(target, f'subject_{idx}') != getattr(row, f'rank_{idx}')
                        )
                    fields_not_match.append(target.average != row.rank_average)

                    if any(fields_not_match):
                        for idx in range(subject_count):
                            setattr(target, f'subject_{idx}', getattr(row, f'rank_{idx}'))
                        target.average = row.rank_average
                        target.participants = participants
                        list_update.append(target)

        update_fields = ['subject_0', 'subject_1', 'subject_2', 'subject_3', 'average', 'participants']
        return bulk_create_or_update(rank_model, list_create, list_update, update_fields)

    def update_ranks(self, qs_student):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '등수를 업데이트했습니다.',
            False: '기존 등수와 일치합니다.',
        }
        model_dict = {
            'total': self.rank_total_model,
            'department': self.rank_category_model,
        }

        is_updated_list = [
            self.update_rank_model(qs_student, model_dict, 'total'),
            self.update_rank_model(qs_student, model_dict, 'department'),
        ]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def get_data_statistics(self):
        qs_students = (
            self.student_model.objects.filter(psat=self.exam.psat)
            .select_related('psat', 'category', 'score', 'rank_total', 'rank_category')
            .annotate(
                department=F('category__department'),
                subject_0=F('score__subject_0'),
                subject_1=F('score__subject_1'),
                subject_2=F('score__subject_2'),
                subject_3=F('score__subject_3'),
                average=F('score__average'),
            )
        )

        department_list = list(
            self.category_model.objects.filter(exam=self.exam.psat.exam).order_by('order')
            .values_list('department', flat=True)
        )
        department_list.insert(0, '전체')

        data_statistics = []
        score_list = {}
        for department in department_list:
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
            department_idx = department_list.index(department)
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

    def update_statistics_model(self, data_statistics):
        model = self.statistics_model
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '통계를 업데이트했습니다.',
            False: '기존 통계와 일치합니다.',
        }
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
                new_query = model.objects.get(psat=self.exam.psat, department=department)
                fields_not_match = any(
                    getattr(new_query, fld) != val for fld, val in stat_dict.items()
                )
                if fields_not_match:
                    for fld, val in stat_dict.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except model.DoesNotExist:
                list_create.append(model(psat=self.exam.psat, **stat_dict))
        update_fields = [
            'department', 'subject_0', 'subject_1', 'subject_2', 'subject_3', 'average',
        ]
        is_updated = bulk_create_or_update(model, list_create, list_update, update_fields)
        return is_updated, message_dict[is_updated]

    @staticmethod
    def update_answer_count_model(model_dict, rank_type='all'):
        answer_model = model_dict['answer']
        answer_count_model = model_dict[rank_type]

        list_update = []
        list_create = []

        lookup_field = f'student__rank_total__average'
        top_rank_threshold = 0.27
        mid_rank_threshold = 0.73
        participants_function = F('student__rank_total__participants')

        lookup_exp = {}
        if rank_type == 'top':
            lookup_exp[f'{lookup_field}__lte'] = participants_function * top_rank_threshold
        elif rank_type == 'mid':
            lookup_exp[f'{lookup_field}__gt'] = participants_function * top_rank_threshold
            lookup_exp[f'{lookup_field}__lte'] = participants_function * mid_rank_threshold
        elif rank_type == 'low':
            lookup_exp[f'{lookup_field}__gt'] = participants_function * mid_rank_threshold

        answer_distribution = (
            answer_model.objects.filter(**lookup_exp)
            .select_related('student', 'student__rank_total')
            .values('problem_id', 'answer')
            .annotate(count=Count('id')).order_by('problem_id', 'answer')
        )
        organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

        for entry in answer_distribution:
            problem_id = entry['problem_id']
            answer = entry['answer']
            count = entry['count']
            organized_distribution[problem_id][answer] = count

        count_fields = [
            'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
        ]
        for problem_id, answers_original in organized_distribution.items():
            answers = {'count_multiple': 0}
            for answer, count in answers_original.items():
                if answer <= 5:
                    answers[f'count_{answer}'] = count
                else:
                    answers['count_multiple'] = count
            answers['count_sum'] = sum(answers[fld] for fld in count_fields)

            try:
                new_query = answer_count_model.objects.get(problem_id=problem_id)
                fields_not_match = any(
                    getattr(new_query, fld) != val for fld, val in answers.items()
                )
                if fields_not_match:
                    for fld, val in answers.items():
                        setattr(new_query, fld, val)
                    list_update.append(new_query)
            except answer_count_model.DoesNotExist:
                list_create.append(answer_count_model(problem_id=problem_id, **answers))
        update_fields = [
            'problem_id', 'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
            'count_sum'
        ]
        return bulk_create_or_update(answer_count_model, list_create, list_update, update_fields)

    def update_answer_counts(self):
        message_dict = {
            None: '에러가 발생했습니다.',
            True: '문항분석표를 업데이트했습니다.',
            False: '기존 문항분석표 데이터와 일치합니다.',
        }

        model_dict = {
            'answer': self.answer_model,
            'all': self.answer_count_model,
            'top': self.answer_count_top_model,
            'mid': self.answer_count_mid_model,
            'low': self.answer_count_low_model,
        }

        is_updated_list = [
            self.update_answer_count_model(model_dict, 'all'),
            self.update_answer_count_model(model_dict, 'top'),
            self.update_answer_count_model(model_dict, 'mid'),
            self.update_answer_count_model(model_dict, 'low'),
        ]

        if None in is_updated_list:
            is_updated = None
        elif any(is_updated_list):
            is_updated = True
        else:
            is_updated = False
        return is_updated, message_dict[is_updated]

    def create_default_answer_counts(self, problems):
        model_set = {
            'all': self.answer_count_model,
            'top': self.answer_count_top_model,
            'mid': self.answer_count_mid_model,
            'low': self.answer_count_low_model,
        }
        for rank_type, model in model_set.items():
            list_create = []
            if model:
                for problem in problems:
                    try:
                        model.objects.get(problem=problem)
                    except model.DoesNotExist:
                        list_create.append(model(problem=problem))
            bulk_create_or_update(model, list_create, [], [])

    def create_default_statistics(self):
        model = self.statistics_model
        department_list = list(
            self.category_model.objects.filter(exam=self.exam.psat.exam).order_by('order')
            .values_list('department', flat=True)
        )
        department_list.insert(0, '전체')

        list_create = []
        if model:
            for department in department_list:
                try:
                    model.objects.get(psat=self.exam.psat, department=department)
                except model.DoesNotExist:
                    list_create.append(model(psat=self.exam.psat, department=department))
        bulk_create_or_update(model, list_create, [], [])


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated
