__all__ = [
    'NormalListData', 'NormalDetailData', 'NormalAnswerProcessData',
    'AdminListData', 'AdminDetailData',
    'AdminCreateCurriculumData', 'AdminCreateStudentData',
    'AdminUploadCategoryData', 'AdminUploadCurriculumData', 'AdminUploadAnswerData',
    'AdminUpdateData',
]

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta

import pandas as pd
from django.db.models import F, QuerySet
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import reswap

from a_psat import models, forms
from a_psat.utils.variables import RequestData
from common.utils import get_paginator_context, HtmxHttpRequest, update_context_data
from common.utils.export_excel_methods import *
from common.utils.modify_models_methods import *

UPDATE_MESSAGES = {
    'score': get_update_messages('점수'),
    'rank': get_update_messages('등수'),
    'statistics': get_update_messages('통계'),
    'answer_count': get_update_messages('문항분석표'),
}


@dataclass(kw_only=True)
class NormalListData:
    request: HtmxHttpRequest

    def get_student_context(self):
        student_context = None
        if self.request.user.is_authenticated:
            student_context = models.StudyStudent.objects.get_filtered_qs_by_user(self.request.user)

            qs_curriculum_schedule_info = models.StudyCurriculumSchedule.objects.schedule_info()
            schedule_info = defaultdict()
            for qs_cs in qs_curriculum_schedule_info:
                schedule_info[qs_cs['curriculum']] = qs_cs

            for qs_s in student_context:
                qs_s.study_rounds = schedule_info[qs_s.curriculum_id]['study_rounds']
                qs_s.earliest_datetime = schedule_info[qs_s.curriculum_id]['earliest']
                qs_s.latest_datetime = schedule_info[qs_s.curriculum_id]['latest']
        return student_context


@dataclass(kw_only=True)
class NormalDetailData:
    request: HtmxHttpRequest
    student: models.StudyStudent

    def __post_init__(self):
        # 외부 클래스 호출
        self.current_time = timezone.now()
        request_data = RequestData(request=self.request)

        # 내부 변수 정의
        self._schedule = models.StudyCurriculumSchedule.objects.open_curriculum_schedule(
            self.student.curriculum, self.current_time)
        self._homework_schedule = self.get_homework_schedule()
        self._opened_rounds = self._schedule.values_list('lecture_round', flat=True)
        self._score_dict = self.get_score_dict()

        # 외부 호출 변수 정의
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

        self.statistics = self.get_curriculum_statistics()
        self.my_results = models.StudyResult.objects.opened_round_student_results(self.student, self._opened_rounds)
        self.lecture_context = get_study_lecture_context(self._schedule, self.page_number)

    def get_homework_schedule(self):
        homework_schedule = defaultdict(dict)
        for obj in self._schedule:
            if obj.lecture_round:
                homework_schedule[obj.lecture_round]['lecture_datetime'] = obj.lecture_datetime
                homework_schedule[obj.lecture_round]['lecture_open_datetime'] = obj.lecture_open_datetime
            if obj.homework_round:
                homework_schedule[obj.homework_round]['homework_end_datetime'] = obj.homework_end_datetime
        return homework_schedule

    def get_score_dict(self):
        # 점수 계산용 비어 있는 딕셔너리 만들기 (score_1: 언어, score_2: 자료, score_3: 상황)
        score_dict = defaultdict(dict)
        for study_round in range(self.student.curriculum.category.round + 1):
            key = study_round if study_round else 'total'
            score_dict[key]['score_sum'] = 0  # 총점 합계
            for i in range(4):
                score_dict[key][f'score_{i}'] = 0  # 과목별 총점

        # 과목별 점수 업데이트 (쿼리셋 주석으로 처리한 과목 필드(subject_1 등)를 성적 필드(score_1 등)로 변환)
        qs_answer = models.StudyAnswer.objects.answers_with_correct(self.student)
        for qs_a in qs_answer:
            if qs_a['is_correct']:
                score_field = str(qs_a['subject']).replace('subject', 'score')
                score_dict[qs_a['round']]['score_sum'] += 1
                score_dict[qs_a['round']][score_field] += 1
                score_dict['total']['score_sum'] += 1
                score_dict['total'][score_field] += 1
        return score_dict

    def get_my_result_context(self):
        context = get_paginator_context(self.my_results, self.page_number, 4)

        # 전체 등수 및 통계
        context['total'] = self.get_my_total_result()

        # 회차별 등수 및 통계, 스케줄 자료
        score_dict_for_rank = self.get_score_dict_for_rank()
        for obj in context['page_obj']:
            for key, val in self._score_dict[obj.psat.round].items():
                setattr(obj, key, val)

            obj.rank = score_dict_for_rank[obj.psat.round].index(obj.score) + 1 if obj.score else None
            stat = self.statistics['per_round'].get(obj.psat.round)
            obj.participants = stat['participants'] if stat else None
            obj.schedule = self._homework_schedule.get(obj.psat.round)
        return context

    def get_my_total_result(self):
        qs_rank = models.StudyStudent.objects.annotate_curriculum_rank(self.student.curriculum)
        rank = None
        for qs_r in qs_rank:
            if qs_r.id == self.student.id:
                rank = qs_r.rank

        total_stat = self.statistics['total']
        problem_count = models.StudyProblem.objects.opened_category_problem_count(
            self.student.curriculum.category, self._opened_rounds)
        my_total_result = {
            'total_score_sum': problem_count,
            'score_sum': self._score_dict['total']['score_sum'],
            'participants': total_stat['participants'],
            'rank': rank if self._score_dict['total']['score_sum'] else None,
        }
        for i in range(4):
            my_total_result[f'score_{i}'] = self._score_dict['total'][f'score_{i}']
        return my_total_result

    def get_score_dict_for_rank(self):
        qs_score = models.StudyResult.objects.opened_round_scores(self.student.curriculum, self._opened_rounds)
        score_dict_for_rank = defaultdict(list)
        for qs_s in qs_score:
            score = qs_s['score']
            if score is not None:
                score_dict_for_rank[qs_s['round']].append(score)
        for rnd, score_list in score_dict_for_rank.items():
            score_dict_for_rank[rnd] = sorted(score_list, reverse=True)
        return score_dict_for_rank

    def get_curriculum_statistics(self):
        qs_student = models.StudyStudent.objects.students_with_results_in_curriculum(self.student.curriculum)
        total_stat = get_study_score_stat_dict(qs_student)
        data_statistics = get_study_data_statistics(qs_student)
        per_round_stat = {}
        for data in data_statistics:
            per_round_stat[data['study_round']] = data
        return {
            'total': total_stat,
            'per_round': per_round_stat,
        }

    def get_statistics_context(self):
        per_round_stat = self.statistics['per_round']
        context = get_paginator_context(self.my_results, self.page_number, 4)
        for obj in context['page_obj']:
            data_stat = per_round_stat.get(obj.psat.round)
            if data_stat:
                for key, val in data_stat.items():
                    setattr(obj, key, val)

            obj.statistics = data_stat
            obj.schedule = self._homework_schedule.get(obj.psat.round)
        return context

    def get_answer_context(self):
        qs_problem = models.StudyProblem.objects.annotate_answer_count_in_category(
            self.student.curriculum.category).filter(psat__round__in=self._opened_rounds).order_by('-psat')
        context = get_paginator_context(qs_problem, self.page_number, on_each_side=1)

        homework_rounds = []
        for obj in context['page_obj']:
            homework_rounds.append(obj.psat.round)

        qs_answer = models.StudyAnswer.objects.answers_in_homework_rounds(self.student, homework_rounds)
        answer_student_dict = defaultdict(dict)
        for qs_a in qs_answer:
            answer_student_dict[(qs_a.problem.psat.round, qs_a.problem.number)] = qs_a.answer

        for obj in context['page_obj']:
            obj: models.StudyProblem

            ans_student = answer_student_dict[(obj.psat.round, obj.number)]
            ans_official = obj.answer
            answer_official_list = [int(digit) for digit in str(ans_official)]

            obj.schedule = self._homework_schedule.get(obj.psat.round)
            obj.no = obj.number
            obj.ans_student = ans_student
            obj.ans_student_circle = models.choices.answer_choice()[ans_student] if ans_student else None
            obj.ans_official = ans_official
            obj.ans_official_circle = obj.problem.get_answer_display()
            obj.is_correct = ans_student in answer_official_list
            obj.ans_list = answer_official_list
            obj.rate_correct = obj.answer_count.get_answer_rate(ans_official)
            obj.rate_correct_top = obj.answer_count_top_rank.get_answer_rate(ans_official)
            obj.rate_correct_mid = obj.answer_count_mid_rank.get_answer_rate(ans_official)
            obj.rate_correct_low = obj.answer_count_low_rank.get_answer_rate(ans_official)
            try:
                obj.rate_gap = obj.rate_correct_top - obj.rate_correct_low
            except TypeError:
                obj.rate_gap = None

        return context


@dataclass(kw_only=True)
class NormalAnswerProcessData:
    request: HtmxHttpRequest
    result: models.StudyResult

    def __post_init__(self):
        self.current_time = timezone.now()
        self.psat = self.result.psat
        self.student = self.result.student
        self.problem_count = self.result.psat.problems.count()
        self.answer_data = self.get_answer_data()
        self.is_confirmed = all(self.answer_data)

    def get_answer_data(self):
        empty_answer_data = [0 for _ in range(self.problem_count)]
        answer_data_cookie = self.request.COOKIES.get('answer_data_set', '{}')
        answer_data = json.loads(answer_data_cookie) or empty_answer_data
        return answer_data

    def get_answer_student(self):
        return [{'no': no, 'ans': ans} for no, ans in enumerate(self.answer_data, start=1)]

    def process_post_request_to_submit_answer(self, context):
        try:
            no = int(self.request.POST.get('number'))
            ans = int(self.request.POST.get('answer'))
        except Exception as e:
            print(e)
            return reswap(HttpResponse(''), 'none')

        context = update_context_data(context, answer={'no': no, 'ans': ans})
        response = render(self.request, 'a_psat/snippets/predict_answer_button.html', context)

        if 1 <= no <= self.problem_count and 1 <= ans <= 5:
            self.answer_data[no - 1] = ans
            response.set_cookie('answer_data_set', json.dumps(self.answer_data), max_age=3600)
            return response
        else:
            print('Answer is not appropriate.')
            return reswap(HttpResponse(''), 'none')

    def process_post_request_to_confirm_answer(self):
        if self.is_confirmed:
            list_create = []
            for no, ans in enumerate(self.answer_data, start=1):
                problem = models.StudyProblem.objects.get(psat=self.psat, number=no)
                list_create.append(models.StudyAnswer(student=self.student, problem=problem, answer=ans))
            bulk_create_or_update(models.StudyAnswer, list_create, [], [])

            qs_answer_count = models.StudyAnswerCount.objects.get_filtered_qs_by_psat(self.psat)
            for qs_ac in qs_answer_count:
                ans_student = self.answer_data[qs_ac.problem.number - 1]
                setattr(qs_ac, f'count_{ans_student}', F(f'count_{ans_student}') + 1)
                setattr(qs_ac, f'count_sum', F(f'count_sum') + 1)
                qs_ac.save()

            qs_answer = models.StudyAnswer.objects.filter(student=self.student, problem__psat=self.psat)
            score = 0
            for qs_a in qs_answer:
                answer_correct_list = {int(digit) for digit in str(qs_a.answer_correct)}
                if qs_a.answer in answer_correct_list:
                    score += 1
            self.result.score = score
            self.result.save()

            student = self.result.student
            student.score_total = score if student.score_total is None else F('score_total') + score
            student.save()


@dataclass(kw_only=True)
class AdminListData:
    request: HtmxHttpRequest

    def __post_init__(self):
        # 외부 클래스 호출
        request_data = RequestData(request=self.request)

        # 외부 호출 변수 정의
        self.sub_title = request_data.get_sub_title()
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number

    def get_list_context(self, is_category: bool):
        model = models.StudyCategory if is_category else models.StudyCurriculum
        target_list = model.objects.annotate_student_count()
        context = get_paginator_context(target_list, self.page_number)
        for obj in context['page_obj']:
            if is_category:
                qs_student = models.StudyStudent.objects.filter(curriculum__category=obj, score_total__isnull=False)
            else:
                qs_student = models.StudyStudent.objects.filter(curriculum=obj, score_total__isnull=False)
            score_list = qs_student.values_list('score_total', flat=True)
            participants = len(score_list)
            sorted_scores = sorted(score_list, reverse=True)
            if sorted_scores:
                top_10_threshold = max(1, int(participants * 0.10))
                top_25_threshold = max(1, int(participants * 0.25))
                top_50_threshold = max(1, int(participants * 0.50))
                obj.max = sorted_scores[0]
                obj.t10 = sorted_scores[top_10_threshold - 1]
                obj.t25 = sorted_scores[top_25_threshold - 1]
                obj.t50 = sorted_scores[top_50_threshold - 1]
                obj.avg = round(sum(score_list) / participants, 1)
        return context


@dataclass(kw_only=True)
class AdminDetailData:
    request: HtmxHttpRequest
    category: models.StudyCategory
    curriculum: models.StudyCurriculum | None

    def __post_init__(self):
        # 외부 클래스 호출
        request_data = RequestData(request=self.request)

        # 외부 호출 변수 정의
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.student_name = request_data.student_name

        self.qs_schedule = self.get_qs_schedule()
        self.qs_student = self.get_qs_student()
        self.result_count_dict = self.get_result_count_dict()
        self.study_rounds = '1' * self.category.round
        self.qs_problem = self.get_qs_problem_for_context()

        self.qs_psat = self.get_qs_psat_for_context()

        self.lecture_context = get_study_lecture_context(self.qs_schedule, self.page_number)
        self.category_stat = get_study_score_stat_dict(self.qs_student)
        self.statistics_context = get_paginator_context(self.qs_psat, self.page_number)
        self.catalog_context = get_paginator_context(
            self.qs_student, self.page_number, result_count=self.result_count_dict)
        self.answer_context = get_paginator_context(self.qs_problem, self.page_number)
        self.problem_context = get_paginator_context(self.qs_problem, self.page_number)

    def get_qs_schedule(self):
        if self.curriculum:
            return models.StudyCurriculumSchedule.objects.filter(curriculum=self.curriculum).order_by('-lecture_number')

    def get_qs_student(self):
        if self.curriculum:
            qs_student = models.StudyStudent.objects.students_with_results_in_curriculum(self.curriculum)
        else:
            qs_student = models.StudyStudent.objects.students_with_results_in_category(self.category)
        if self.student_name:
            qs_student = qs_student.filter(name=self.student_name)
        return qs_student

    def get_result_count_dict(self):
        if self.curriculum:
            return models.StudyResult.objects.get_result_count_dict_by_curriculum(self.curriculum)
        return models.StudyResult.objects.get_result_count_dict_by_category(self.category)

    def get_qs_psat_for_context(self):
        qs_psat = models.StudyPsat.objects.get_qs_psat(self.category)
        if self.curriculum:
            data_statistics = get_study_data_statistics(self.qs_student)
            data_statistics_by_study_round = {}
            for d in data_statistics:
                data_statistics_by_study_round[d['study_round']] = d
            for p in qs_psat:
                p.statistics = data_statistics_by_study_round.get(p.round)
        return qs_psat

    def get_qs_problem_for_context(self):
        qs_problem = models.StudyProblem.objects.annotate_answer_count_in_category(self.category)
        for entry in qs_problem:
            ans_official = entry.ans_official

            answer_official_list = []
            if ans_official > 5:
                answer_official_list = [int(digit) for digit in str(ans_official)]

            entry.no = entry.number
            entry.ans_official = ans_official
            entry.ans_official_circle = entry.problem.get_answer_display()
            entry.ans_list = answer_official_list

            entry.rate_correct = entry.answer_count.get_answer_rate(ans_official)
            entry.rate_correct_top = entry.answer_count_top_rank.get_answer_rate(ans_official)
            entry.rate_correct_mid = entry.answer_count_mid_rank.get_answer_rate(ans_official)
            entry.rate_correct_low = entry.answer_count_low_rank.get_answer_rate(ans_official)
            try:
                entry.rate_gap = entry.rate_correct_top - entry.rate_correct_low
            except TypeError:
                entry.rate_gap = None
        return qs_problem

    def get_statistics_response(self) -> HttpResponse:
        column_label = ['회차', '응시 인원', '최고', '상위 10%', '상위 25%', '상위 50%', '평균']

        statistics = [{"study_round": 0}]
        statistics[0].update(self.category_stat)
        for qs_p in self.qs_psat:
            statistics.append(qs_p.statistics)
        df = pd.DataFrame.from_records(statistics)
        df.columns = column_label

        info = self.curriculum.curriculum_info if self.curriculum else self.category.category_info
        filename = f'{info}_성적통계.xlsx'

        return get_response_for_excel_file(df, filename)

    def get_catalog_response(self) -> HttpResponse:
        column_list = ['id', 'curriculum_id', 'user_id', 'serial', 'name']
        column_label = ['ID', '커리큘럼 ID', '사용자 ID', '수험번호', '이름', '답안 제출횟수']

        student_list = self.qs_student.order_by('serial').values(*column_list)
        for student in student_list:
            student['result_count'] = self.result_count_dict.get(student['id'], 0)
        df = pd.DataFrame.from_records(student_list)
        df.columns = column_label

        info = self.curriculum.curriculum_info if self.curriculum else self.category.category_info
        filename = f'{info}_성적일람표.xlsx'

        return get_response_for_excel_file(df, filename)

    def get_answer_response(self) -> HttpResponse:
        qs_answer_count = models.PredictAnswerCount.objects.filtered_by_psat_and_subject(self.psat)
        filename = f'{self.psat.full_reference}_문항분석표.xlsx'

        df1 = self.get_answer_df_for_excel(qs_answer_count)
        df2 = self.get_answer_df_for_excel(qs_answer_count, True)

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='전체')
            df2.to_excel(writer, sheet_name='필터링')

        return get_response_for_excel_file(df1, filename, excel_data)

    @staticmethod
    def get_answer_df_for_excel(
            qs_answer_count: QuerySet[models.PredictAnswerCount], is_filtered=False) -> pd.DataFrame:
        prefix = 'filtered_' if is_filtered else ''
        column_list = ['id', 'problem_id', 'subject', 'number', 'ans_official', 'ans_predict']
        for rank_type in ['all', 'top', 'mid', 'low']:
            for num in ['1', '2', '3', '4', '5', 'sum']:
                column_list.append(f'{prefix}count_{num}_{rank_type}')

        column_label = [
            ('DB정보', 'ID'), ('DB정보', '문제 ID'),
            ('문제정보', '과목'), ('문제정보', '번호'), ('문제정보', '정답'), ('문제정보', '예상 정답'),
        ]
        for rank_type in ['전체', '상위권', '중위권', '하위권']:
            column_label.extend([
                (rank_type, '①'), (rank_type, '②'), (rank_type, '③'),
                (rank_type, '④'), (rank_type, '⑤'), (rank_type, '합계'),
            ])

        df = pd.DataFrame.from_records(qs_answer_count.values(*column_list))
        df.columns = pd.MultiIndex.from_tuples(column_label)
        return df


@dataclass(kw_only=True)
class AdminCreateCurriculumData:
    request: HtmxHttpRequest

    def __post_init__(self):
        # 외부 클래스 호출
        request_data = RequestData(request=self.request)

        # 변수 정의
        self.view_type = request_data.view_type
        self.form = forms.StudyCurriculumForm(self.request.POST, self.request.FILES)

    def get_category_form(self):
        organization_id = self.request.POST.get('organization')
        organization = models.StudyOrganization.objects.get(id=organization_id)
        semester = self.request.POST.get('semester')
        category_basic = models.StudyCategory.objects.filter(study_type='기본').first()
        category_advanced = models.StudyCategory.objects.filter(study_type='심화').first()
        category_set = {
            ('서울과기대', '1'): category_advanced,
            ('서울과기대', '2'): category_basic,
            ('한국외대', '1'): category_basic,
            ('한국외대', '2'): category_advanced,
        }
        category = category_set.get((organization.name, semester))
        if category:
            category_form = forms.StudyCurriculumCategoryForm(initial={'category': category})
        else:
            category_form = forms.StudyCurriculumCategoryForm()
        return category_form

    def process_post_request(self):
        year = self.form.cleaned_data['year']
        organization = self.form.cleaned_data['organization']
        semester = int(self.form.cleaned_data['semester'])
        category = self.form.cleaned_data['category']
        curriculum_name = models.choices.study_curriculum_name()[organization.name][semester]

        try:
            curriculum = models.StudyCurriculum.objects.get(year=year, organization=organization, semester=semester)
        except models.StudyCurriculum.DoesNotExist:
            curriculum = models.StudyCurriculum.objects.create(
                year=year, organization=organization, semester=semester, category=category, name=curriculum_name)

        self.admin_update_curriculum_schedule_model(curriculum)

    @with_bulk_create_or_update()
    def admin_update_curriculum_schedule_model(self, curriculum):
        lecture_nums = int(self.form.cleaned_data['lecture_nums'])
        lecture_start_datetime = self.form.cleaned_data['lecture_start_datetime']

        list_create, list_update = [], []
        for lecture_number in range(1, lecture_nums + 1):
            if lecture_nums <= 15:
                lecture_theme = lecture_number
            else:
                if lecture_number < 15:
                    lecture_theme = lecture_number
                elif lecture_number == 15:
                    lecture_theme = 0
                else:
                    lecture_theme = 15

            lecture_round, homework_round = None, None
            if 3 <= lecture_number <= 14:
                lecture_round = lecture_number - 2
            if 2 <= lecture_number <= 13:
                homework_round = lecture_number - 1

            lecture_datetime = lecture_start_datetime + timedelta(days=7) * (lecture_number - 1)
            reserved_days_for_open = 14 if lecture_number == 8 else 7
            lecture_open_datetime = lecture_datetime - timedelta(days=reserved_days_for_open)
            lecture_open_datetime = lecture_open_datetime.replace(hour=11, minute=0, second=0)
            homework_end_datetime = (lecture_datetime + timedelta(days=6)).replace(
                hour=23, minute=59, second=59, microsecond=999999)

            find_expr = {'curriculum': curriculum, 'lecture_number': lecture_number}
            matching_expr = {
                'lecture_theme': lecture_theme,
                'lecture_round': lecture_round,
                'homework_round': homework_round,
                'lecture_open_datetime': lecture_open_datetime,
                'homework_end_datetime': homework_end_datetime,
                'lecture_datetime': lecture_datetime,
            }
            try:
                schedule = models.StudyCurriculumSchedule.objects.get(**find_expr)
                fields_not_match = [getattr(schedule, key) != val for key, val in matching_expr.items()]
                if any(fields_not_match):
                    for key, val in matching_expr.items():
                        setattr(schedule, key, val)
                    list_update.append(schedule)
            except models.StudyCurriculumSchedule.DoesNotExist:
                list_create.append(models.StudyCurriculumSchedule(**find_expr, **matching_expr))
        update_fields = [
            'lecture_number', 'lecture_theme', 'lecture_round', 'homework_round',
            'lecture_open_datetime', 'homework_end_datetime', 'lecture_datetime'
        ]
        return models.StudyCurriculumSchedule, list_create, list_update, update_fields


@dataclass(kw_only=True)
class AdminCreateStudentData:
    student: models.StudyStudent

    @with_bulk_create_or_update()
    def create_default_result_instances(self):
        psats = models.StudyPsat.objects.filter(category=self.student.curriculum.category)
        list_create = []
        for psat in psats:
            try:
                models.StudyResult.objects.get(student=self.student, psat=psat)
            except models.StudyResult.DoesNotExist:
                list_create.append(models.StudyResult(student=self.student, psat=psat))
        return models.StudyResult, list_create, [], []


@dataclass(kw_only=True)
class AdminUploadCategoryData:
    request: HtmxHttpRequest

    def __post_init__(self):
        file = self.request.FILES['file']
        self.xls = pd.ExcelFile(file)

    def process_post_request(self):
        if 'category' in self.xls.sheet_names:
            df_category = pd.read_excel(self.xls, sheet_name='category', header=0, index_col=0)
            for _, row in df_category.iterrows():
                self.update_category_and_psat_model(row)
        if 'problem' in self.xls.sheet_names:
            self.update_problem_model()
            self.update_problem_counts()
            self.create_answer_count_model_instances()

    @with_bulk_create_or_update()
    def update_category_and_psat_model(self, row: pd.Series):
        season = row['season']
        study_type = row['study_type']
        name = row['name']
        study_round = row['round']
        update_expr = {'name': name, 'round': study_round}

        category, _ = models.StudyCategory.objects.get_or_create(season=season, study_type=study_type)
        fields_not_match = [getattr(category, k) != v for k, v in update_expr.items()]
        if any(fields_not_match):
            for key, val in update_expr.items():
                setattr(category, key, val)
            category.save()

        list_create, list_update = [], []
        for rnd in range(1, study_round + 1):
            try:
                models.StudyPsat.objects.get(category=category, round=rnd)
            except models.StudyPsat.DoesNotExist:
                list_create.append(models.StudyPsat(category=category, round=rnd))
        return models.StudyPsat, list_create, list_update, []

    @with_bulk_create_or_update()
    def update_problem_model(self):
        df = pd.read_excel(self.xls, sheet_name='problem', header=0)
        psat_dict = self.get_psat_dict()
        problem_dict = self.get_problem_dict()

        list_create, list_update = [], []
        for _, row in df.iterrows():
            season = row['season']
            study_type = row['study_type']
            study_round = row['round']
            round_problem_number = row['round_problem_number']

            year = row['year']
            exam = row['exam']
            subject = row['subject']
            number = row['number']

            psat_key = (season, study_type, study_round)
            problem_key = (season, study_type, study_round, round_problem_number)
            if psat_key in psat_dict and problem_key not in problem_dict:
                psat = psat_dict[psat_key]
                try:
                    problem = models.Problem.objects.get(
                        psat__year=year, psat__exam=exam, subject=subject, number=number)
                    study_problem = models.StudyProblem(
                        psat=psat, number=round_problem_number, problem=problem)
                    list_create.append(study_problem)
                except models.Problem.DoesNotExist:
                    print(f'Problem with {year}{exam}{subject}-{number:02} does not exist.')
        return models.StudyProblem, list_create, list_update, []

    @staticmethod
    def get_psat_dict() -> dict[tuple, models.StudyPsat]:
        psat_dict = {}
        for p in models.StudyPsat.objects.select_related('category'):
            psat_dict[(p.category.season, p.category.study_type, p.round)] = p
        return psat_dict

    @staticmethod
    def get_problem_dict() -> dict[tuple, models.StudyProblem]:
        problem_dict = {}
        for p in models.StudyProblem.objects.select_related('psat', 'psat__category', 'problem', 'problem__psat'):
            problem_dict[(p.psat.category.season, p.psat.category.study_type, p.psat.round, p.number)] = p
        return problem_dict

    @staticmethod
    def update_problem_counts():
        problem_count_list = models.StudyProblem.objects.get_ordered_qs_by_subject_field()
        problem_count_dict = defaultdict(dict)
        for p in problem_count_list:
            problem_count_dict[p['psat_id']][p['subject']] = p['count']
        for psat in models.StudyPsat.objects.all():
            problem_counts = problem_count_dict[psat.id]
            problem_counts['total'] = sum(problem_counts.values())
            psat.problem_counts = problem_counts
            psat.save()

    @staticmethod
    def create_answer_count_model_instances():
        problems = models.StudyProblem.objects.order_by('id')
        model_dict = {
            'answer_count_top': models.StudyAnswerCount,
            'answer_count_top_rank': models.StudyAnswerCountTopRank,
            'answer_count_mid_rank': models.StudyAnswerCountMidRank,
            'answer_count_low_rank': models.StudyAnswerCountLowRank,
        }
        for related_name, model in model_dict.items():
            list_create = []
            for problem in problems:
                if not hasattr(problem, related_name):
                    append_list_create(model, list_create, problem=problem)
            bulk_create_or_update(model, list_create, [], [])


@dataclass(kw_only=True)
class AdminUploadCurriculumData:
    request: HtmxHttpRequest

    def __post_init__(self):
        file = self.request.FILES['file']
        self.xls = pd.ExcelFile(file)

    def process_post_request(self):
        curriculum_dict = self.get_curriculum_dict()
        if 'curriculum' in self.xls.sheet_names:
            self.update_curriculum_model(curriculum_dict)
        if 'student' in self.xls.sheet_names:
            self.update_student_model(curriculum_dict)
            self.update_result_model()

    @with_bulk_create_or_update()
    def update_curriculum_model(self, curriculum_dict: dict):
        df = pd.read_excel(self.xls, sheet_name='curriculum', header=0, index_col=0)
        category_dict = self.get_category_dict()
        organization_dict = self.get_organization_dict()

        list_create, list_update = [], []
        for _, row in df.iterrows():
            organization_name = row['organization_name']
            curriculum_key = (row['organization_name'], row['year'], row['semester'])
            category_key = (row['category_season'], row['category_study_type'])

            if organization_name in organization_dict.keys() and category_key in category_dict.keys():
                organization = organization_dict[organization_name]
                category = category_dict[category_key]

                find_expr = {'organization': organization, 'year': curriculum_key[1], 'semester': curriculum_key[2]}
                update_expr = {'category': category, 'name': row['curriculum_name']}

                if curriculum_key in curriculum_dict.keys():
                    curriculum = curriculum_dict[curriculum_key]
                    fields_not_match = [getattr(curriculum, k) != v for k, v in update_expr.items()]
                    if any(fields_not_match):
                        for key, val in update_expr.items():
                            setattr(curriculum, key, val)
                        list_update.append(curriculum)
                else:
                    list_create.append(models.StudyCurriculum(**find_expr, **update_expr))
        return models.StudyCurriculum, list_create, list_update, ['category', 'name']

    @with_bulk_create_or_update()
    def update_student_model(self, curriculum_dict):
        df = pd.read_excel(self.xls, sheet_name='student', header=0, index_col=0, dtype={'serial': str})
        student_dict = self.get_student_dict()

        list_create, list_update = [], []
        for _, row in df.iterrows():
            year = row['year']
            organization_name = row['organization_name']
            semester = row['semester']
            serial = row['serial']
            name = row['name']

            curriculum_key = (organization_name, year, semester)
            student_key = (organization_name, year, semester, serial)
            if student_key in student_dict.keys():
                student = student_dict[student_key]
                if student.name != name:
                    student.name = name
                    list_update.append(student)
            else:
                if curriculum_key in curriculum_dict.keys():
                    curriculum = curriculum_dict[curriculum_key]
                    list_create.append(
                        models.StudyStudent(curriculum=curriculum, serial=serial, name=name)
                    )
        return models.StudyStudent, list_create, list_update, ['name']

    @with_bulk_create_or_update()
    def update_result_model(self):
        psat_dict: dict[models.StudyCategory, list[models.StudyPsat]] = defaultdict(list)
        for p in models.StudyPsat.objects.with_select_related():
            psat_dict[p.category].append(p)

        result_dict: dict[tuple[models.StudyStudent, models.StudyPsat], models.StudyResult] = defaultdict()
        for r in models.StudyResult.objects.select_related('student', 'psat'):
            result_dict[(r.student, r.psat)] = r

        list_create = []
        for s in models.StudyStudent.objects.with_select_related():
            psats = psat_dict[s.curriculum.category]
            for p in psats:
                if (s, p) not in result_dict.keys():
                    list_create.append(models.StudyResult(student=s, psat=p))
        return models.StudyResult, list_create, [], []

    @staticmethod
    def get_curriculum_dict() -> dict[tuple, models.StudyCurriculum]:
        curriculum_dict = {}
        for c in models.StudyCurriculum.objects.select_related('organization', 'category'):
            curriculum_dict[(c.organization.name, c.year, c.semester)] = c
        return curriculum_dict

    @staticmethod
    def get_student_dict() -> dict[tuple, models.StudyStudent]:
        student_dict = {}
        for s in models.StudyCurriculum.objects.select_related(
                'curriculum', 'curriculum__organization', 'curriculum__category'):
            student_dict[(
                s.curriculum.organization.name, s.curriculum.year, s.curriculum.semester, s.serial
            )] = s
        return student_dict

    @staticmethod
    def get_category_dict() -> dict[tuple, models.StudyCategory]:
        category_dict = {}
        for c in models.StudyCategory.objects.all():
            category_dict[(c.season, c.study_type)] = c
        return category_dict

    @staticmethod
    def get_organization_dict() -> dict[str, models.StudyOrganization]:
        organization_dict = {}
        for o in models.StudyOrganization.objects.all():
            organization_dict[o.name] = o
        return organization_dict


@dataclass(kw_only=True)
class AdminUploadAnswerData:
    request: HtmxHttpRequest
    curriculum: models.StudyCurriculum

    def __post_init__(self):
        file = self.request.FILES['file']
        self.xls = pd.ExcelFile(file)

    def process_post_request(self):
        student_dict = self.get_student_dict()
        df = pd.read_excel(self.xls, header=[0, 1], index_col=0)
        df.fillna(value=0, inplace=True)

        for serial, row in df.iterrows():
            list_create, list_update = [], []
            if str(serial) in student_dict.keys():
                student = student_dict[str(serial)]
                for col in df.columns[1:]:
                    study_round = col[0]
                    number = col[1]
                    answer = row[col]
                    if answer:
                        try:
                            study_answer = models.StudyAnswer.objects.get(
                                student=student,
                                problem__psat__category=self.curriculum.category,
                                problem__psat__round=study_round,
                                problem__number=number
                            )
                            if study_answer.answer != answer:
                                study_answer.answer = answer
                                list_update.append(study_answer)
                        except models.StudyAnswer.DoesNotExist:
                            problem = models.StudyProblem.objects.get(
                                psat__category=self.curriculum.category,
                                psat__round=study_round, number=number
                            )
                            study_answer = models.StudyAnswer(
                                student=student, problem=problem, answer=answer)
                            list_create.append(study_answer)
                        except ValueError as error:
                            print(error)

            bulk_create_or_update(models.StudyAnswer, list_create, list_update, ['answer'])

    def get_student_dict(self) -> dict[str, models.StudyStudent]:
        student_dict = {}
        for s in models.StudyStudent.objects.with_select_related().filter(curriculum=self.curriculum):
            student_dict[s.serial] = s
        return student_dict


@dataclass(kw_only=True)
class AdminUpdateData:
    request: HtmxHttpRequest
    update_target: models.StudyCategory | models.StudyCurriculum

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.view_type = request_data.view_type
        self.qs_student = self.get_qs_student()
        self.qs_category_student = self.get_qs_category_student()
        self.psats = self.get_psats()

    def get_qs_student(self):
        if isinstance(self.update_target, models.StudyCategory):
            return models.StudyStudent.objects.students_with_results_in_category(self.update_target)
        return models.StudyStudent.objects.students_with_results_in_curriculum(self.update_target)

    def get_qs_category_student(self):
        if isinstance(self.update_target, models.StudyCategory):
            return self.qs_student
        return models.StudyStudent.objects.students_with_results_in_category(self.update_target.category)

    def get_psats(self):
        if isinstance(self.update_target, models.StudyCategory):
            return models.StudyPsat.objects.get_qs_psat(self.update_target)
        return models.StudyPsat.objects.get_qs_psat(self.update_target.category)

    @with_update_message(UPDATE_MESSAGES['score'])
    def update_scores(self):
        @with_bulk_create_or_update()
        def get_update_list_of_result_model_for_each_student(student):
            qs_result = models.StudyResult.objects.filter(student=student, psat__in=self.psats)
            list_create, list_update = [], []
            for qs_r in qs_result:
                qs_answer = models.StudyAnswer.objects.filter(student=qs_r.student, problem__psat=qs_r.psat)
                if not qs_answer.exists():
                    score = None
                else:
                    score = 0
                    for qs_a in qs_answer:
                        answer_correct_list = {int(digit) for digit in str(qs_a.answer_correct)}
                        if qs_a.answer in answer_correct_list:
                            score += 1
                if qs_r.score != score:
                    qs_r.score = score
                    list_update.append(qs_r)
            return models.StudyResult, list_create, list_update, ['score']

        @with_bulk_create_or_update()
        def get_update_list_of_student_model_for_score_total():
            list_create, list_update = [], []
            student_scores = models.get_study_student_score_calculated_annotation(self.qs_student)
            for student in student_scores:
                if student.score_total != student.score_calculated:
                    student.score_total = student.score_calculated
                    list_update.append(student)
            return models.StudyStudent, list_create, list_update, ['score_total']

        update_list = []
        for student in self.qs_student:
            update_list.append(get_update_list_of_result_model_for_each_student(student))
        update_list.append(get_update_list_of_student_model_for_score_total())

        return update_list

    @with_update_message(UPDATE_MESSAGES['rank'])
    def update_ranks(self):
        @with_bulk_create_or_update()
        def get_update_rank_list_of_result_model():
            list_create, list_update = [], []
            ranked_results = models.StudyResult.objects.get_rank_calculated(self.qs_category_student, self.psats)
            for result in ranked_results:
                if result.rank_calculated != models.StudyResult.objects.get(id=result.id).rank:
                    result.rank = result.rank_calculated
                    list_update.append(result)
            return models.StudyResult, list_create, list_update, ['rank']

        @with_bulk_create_or_update()
        def get_update_rank_total_list_of_student_model():
            list_create, list_update = [], []
            ranked_students = models.get_study_student_total_rank_calculated_annotation(self.qs_category_student)
            for student in ranked_students:
                if student.rank_total != student.rank_calculated:
                    student.rank_total = student.rank_calculated
                    list_update.append(student)
            return models.StudyStudent, list_create, list_update, ['rank_total']

        return [
            get_update_rank_list_of_result_model(),
            get_update_rank_total_list_of_student_model()
        ]

    @with_update_message(UPDATE_MESSAGES['statistics'])
    def update_statistics(self):
        data_statistics = get_study_data_statistics(self.qs_category_student)
        if isinstance(self.update_target, models.StudyCategory):
            category = self.update_target
        else:
            category = self.update_target.category

        @with_bulk_create_or_update()
        def get_update_list_of_statistics_model():
            model = models.StudyPsat
            list_create, list_update = [], []

            round_num = models.StudyPsat.objects.filter(category=category).count()
            participants_num = models.StudyStudent.objects.filter(curriculum__category=category).count()
            if category.round != round_num or category.participants != participants_num:
                category.round = round_num
                category.participants = participants_num
                category.save()
                category.refresh_from_db()

            for data_stat in data_statistics[1:]:
                study_round = data_stat['study_round']
                try:
                    new_query = model.objects.get(category=category, round=study_round)
                    fields_not_match = any(
                        new_query.statistics.get(fld) != val for fld, val in data_stat.items()
                    )
                    if fields_not_match:
                        new_query.statistics = data_stat
                        list_update.append(new_query)
                except model.DoesNotExist:
                    list_create.append(model(category=category, **data_stat))
            return model, list_create, list_update, ['statistics']

        return [get_update_list_of_statistics_model()]

    @with_update_message(UPDATE_MESSAGES['answer_count'])
    def update_answer_counts(self):
        model_dict = {
            'all': models.StudyAnswerCount, 'top': models.StudyAnswerCountTopRank,
            'mid': models.StudyAnswerCountMidRank, 'low': models.StudyAnswerCountLowRank,
        }
        count_fields = [
            'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_multiple',
        ]

        @with_bulk_create_or_update()
        def get_update_list_of_answer_count_model(rank_type):
            answer_count_model = model_dict[rank_type]
            list_create, list_update = [], []

            answer_distribution = models.StudyAnswer.objects.get_study_answer_distribution(rank_type)
            organized_distribution = defaultdict(lambda: {i: 0 for i in range(6)})

            for entry in answer_distribution:
                problem_id = entry['problem_id']
                answer = entry['answer']
                count = entry['count']
                organized_distribution[problem_id][answer] = count

            for problem_id, answers_original in organized_distribution.items():
                update_data = {'count_multiple': 0}
                for answer, count in answers_original.items():
                    if answer <= 5:
                        update_data[f'count_{answer}'] = count
                    else:
                        update_data['count_multiple'] = count
                update_data['count_sum'] = sum(update_data[fld] for fld in count_fields)

                try:
                    new_query = answer_count_model.objects.get(problem_id=problem_id)
                    fields_not_match = any(
                        getattr(new_query, fld) != val for fld, val in update_data.items()
                    )
                    if fields_not_match:
                        for fld, val in update_data.items():
                            setattr(new_query, fld, val)
                        list_update.append(new_query)
                except answer_count_model.DoesNotExist:
                    list_create.append(answer_count_model(problem_id=problem_id, **update_data))
            update_fields = [
                'problem_id', 'count_0', 'count_1', 'count_2', 'count_3',
                'count_4', 'count_5', 'count_multiple', 'count_sum',
            ]
            return answer_count_model, list_create, list_update, update_fields

        return [
            get_update_list_of_answer_count_model('all'),
            get_update_list_of_answer_count_model('top'),
            get_update_list_of_answer_count_model('mid'),
            get_update_list_of_answer_count_model('low'),
        ]


def get_study_data_statistics(qs_student):
    data_statistics = []
    score_dict = defaultdict(list)
    for student in qs_student:
        if student.score_total is not None:
            score_dict['전체'].append(student.score_total)
        for r in student.result_list:
            if r.score is not None:
                score_dict[r.psat.round].append(r.score)

    for study_round, scores in score_dict.items():
        participants = len(scores)
        sorted_scores = sorted(scores, reverse=True)

        def get_top_score(percentage):
            if sorted_scores:
                threshold = max(1, int(participants * percentage))
                return sorted_scores[threshold - 1]

        data_statistics.append({
            'study_round': study_round,
            'participants': participants,
            'max': sorted_scores[0] if sorted_scores else None,
            't10': get_top_score(0.10),
            't25': get_top_score(0.25),
            't50': get_top_score(0.50),
            'avg': round(sum(scores) / participants, 1) if sorted_scores else None,
        })
    return data_statistics


def get_study_lecture_context(qs_schedule, page_number=1, per_page=4):
    context = get_paginator_context(qs_schedule, page_number, per_page)
    lecture_dict = {}
    for lec in models.Lecture.objects.all():
        lecture_dict[(lec.subject, lec.order)] = lec.id

    if context:
        for obj in context['page_obj']:
            obj: models.StudyCurriculumSchedule
            theme = obj.get_lecture_theme_display()

            lecture_id = color_code = None
            if '언어' in theme:
                color_code = 'primary'
                lecture_id = lecture_dict[('언어', int(theme[-1]))]
            elif '자료' in theme:
                color_code = 'success'
                lecture_id = lecture_dict[('자료', int(theme[-1]))]
            elif '상황' in theme:
                color_code = 'warning'
                lecture_id = lecture_dict[('상황', int(theme[-1]))]
            elif '시험' in theme:
                color_code = 'danger'
            obj.color_code = color_code
            obj.lecture_topic = models.choices.study_lecture_topic().get(obj.get_lecture_theme_display())
            if lecture_id:
                obj.url_lecture = reverse_lazy('psat:lecture-detail', args=[lecture_id])
            if '공부법' in theme:
                lecture_ids = [lecture_dict[('공부', i)] for i in range(1, 4)]
                obj.url_lecture_list = [
                    reverse_lazy('psat:lecture-detail', args=[l_id]) for l_id in lecture_ids
                ]
        return context


def get_study_score_stat_dict(qs_student) -> dict:
    # stat_dict keys: participants, max, avg, t10, t25, t50
    stat_dict = models.get_study_statistics_aggregation(qs_student)
    participants = stat_dict['participants']
    if participants != 0:
        score_list = list(qs_student.values_list('score_total', flat=True))

        def get_score(rank_rate: float):
            threshold = max(1, int(participants * rank_rate))
            return score_list[threshold] if threshold < participants else None

        stat_dict['t10'] = get_score(0.10)
        stat_dict['t25'] = get_score(0.25)
        stat_dict['t50'] = get_score(0.50)
    return stat_dict
