import io
import json
import traceback
import zipfile
from urllib.parse import quote

import django.db.utils
import gspread
import pandas as pd
import pdfkit
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import Rank, PercentRank
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from oauth2client.service_account import ServiceAccountCredentials

from common.constants.icon_set import ConstantIconSet
from common.models import User
from score.models import PrimeAnswer
from score import serializers
from .base_mixins import AdminBaseMixin
from ..utils import get_dict_by_sub


class OnlyStaffAllowedMixin(LoginRequiredMixin, UserPassesTestMixin):
    request: any

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('prime:list'))


class TestViewMixin(ConstantIconSet, AdminBaseMixin):
    sub_title: str
    answer_data: dict
    count_total: int

    def get_properties(self):
        super().get_properties()

        self.sub_title: str = self.get_sub_title()
        self.count_total = self.get_count_total()
        self.answer_data = self.get_answer_data()

    def get_sub_title(self) -> str:
        return f'제{self.round}회 {self.exam_name} 테스트 페이지'

    @staticmethod
    def get_prime_answer_qs():
        return PrimeAnswer.objects.filter(student__year=2024, student__round=1)

    def get_count_total(self):
        return self.get_prime_answer_qs().distinct().values('student_id').count()

    def get_answer_data(self) -> dict:
        prime_answer = (
            self.get_prime_answer_qs().annotate(sub=F('prime__subject__abbr')).values()
        )
        answer_data = self.get_empty_answer_data()

        for student in prime_answer:
            sub = student['sub']
            problem_count = self.problem_count_dict[sub]
            for i in range(problem_count):
                ans = student[f'prob{i + 1}']
                if ans in range(1, 6):
                    answer_data[sub][i]['answer'][ans - 1]['count'] += 1

        if self.count_total:
            for sub, problems in answer_data.items():
                for problem in problems:
                    answer_count = []
                    for answer in problem['answer']:
                        answer_count.append(answer['count'])
                        percentage = round(answer['count'] * 100 / self.count_total)
                        answer['percentage'] = percentage
                        if percentage >= 80:
                            answer['status'] = 4  # 정답 예상
                        elif percentage >= 50:
                            answer['status'] = 3  # 정답 유력
                        elif percentage >= 20:
                            answer['status'] = 2  # 정답 보류
                        elif percentage > 0:
                            answer['status'] = 1  # 오답 예상
                    answer_predict_index = answer_count.index(max(answer_count))
                    answer_predict = answer_predict_index + 1
                    answer_percentage = problem['answer'][answer_predict_index]['percentage']
                    problem['answer_predict'] = answer_predict
                    problem['answer_percentage'] = answer_percentage
        return answer_data


class ListViewMixin(ConstantIconSet, AdminBaseMixin):
    sub_title: str
    exam_page_obj: any
    exam_page_range: any

    student_page_obj: any
    student_page_range: any
    student_base_url: str
    student_pagination_url: str

    participant_list: dict
    participant_page_obj: any
    participant_page_range: any

    def get_properties(self):
        super().get_properties()

        self.sub_title = f'{self.exam_name} 관리자 페이지'
        self.exam_page_obj, self.exam_page_range = self.get_paginator_info(self.exam_list)

        self.student_page_obj, self.student_page_range = self.get_paginator_info(self.student_list)
        self.student_base_url = reverse_lazy('predict_admin:list_student')
        self.student_pagination_url = f'{self.student_base_url}?'

        # self.participant_list = self.get_participant_list()
        # self.participant_page_obj, self.participant_page_range = self.get_paginator_info(self.participant_list)

    def get_paginator_info(self, data) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        paginator = Paginator(data, 10)
        page_obj: list[dict] = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_participant_list(self):
        all_user_ids = self.student_model.objects.values('user_id').distinct()
        participant_list = []
        for user_id in all_user_ids:
            participant_list.append(
                {
                    f'user_{user_id}': {
                        'user_id': user_id,
                        'username': User.objects.get(id=user_id).username,
                    }
                }
            )
        for student in self.student_list:
            user_id = student['user_id']
            for exam in self.exam_list:
                code = exam['code']
                participant_list[f'user_{user_id}'][code] = False
                if exam['category'] == student['category'] and exam['year'] == exam['year'] and \
                        exam['ex'] == student['ex'] and exam['round'] == student['round']:
                    participant_list[f'user_{user_id}'][code] = True
        return participant_list


class DetailViewMixin(ConstantIconSet, AdminBaseMixin):
    sub_title: str
    statistics: list
    answer_count_analysis: dict
    page_obj: any
    page_range: any
    student_ids: list
    base_url: str
    pagination_url: str

    def get_properties(self):
        super().get_properties()

        self.sub_title = self.get_sub_title()

        self.statistics = self.get_statistics()
        self.answer_count_analysis = self.get_answer_count_analysis()

        self.page_obj, self.page_range, self.student_ids = self.get_paginator_info()
        self.base_url = reverse_lazy(
            'predict_admin:catalog', args=[self.category, self.year, self.ex, self.round])
        self.pagination_url = f'{self.base_url}?'

    def get_sub_title(self):
        if self.category == 'Prime':
            return f'제{self.round}회 {self.exam_name} 성적 예측'
        return f'{self.year}년 {self.exam_name} 성적 예측'

    def get_answer_count_analysis(self):
        answer_count = (
            self.answer_count_model.objects
            .filter(category=self.category, year=self.year, ex=self.ex, round=self.round)
            .order_by('sub', 'number')
            .values(
                'sub', 'number',
                'count_total', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0',
                'rate_1', 'rate_2', 'rate_3', 'rate_4', 'rate_5', 'rate_0')
        )
        filename = self.get_answer_filename()
        answer_correct_dict = self.get_answer_correct_dict(filename)

        for problem in answer_count:
            sub = problem['sub']  # 과목
            number = problem['number']  # 문제 번호
            ans_number_correct = answer_correct_dict[sub][number - 1]['ans_number']

            if ans_number_correct in range(1, 6):
                rate_correct = problem[f'rate_{ans_number_correct}']
            else:
                answer_correct_list = [int(digit) for digit in str(ans_number_correct)]
                try:
                    rate_correct = sum(problem[f'rate_{ans}'] for ans in answer_correct_list)
                except TypeError:
                    rate_correct = 0
            problem['answer_correct'] = ans_number_correct
            problem['rate_correct'] = rate_correct

            answer_count_list = []  # list for counting answers
            for i in range(5):
                ans_number = i + 1
                answer_count_list.append(problem[f'count_{ans_number}'])
            ans_number_predict = answer_count_list.index(max(answer_count_list)) + 1  # 예상 정답
            rate_accuracy = problem[f'rate_{ans_number_predict}']  # 정확도
            problem['answer_predict'] = ans_number_predict
            problem['rate_accuracy'] = rate_accuracy

        return get_dict_by_sub(answer_count)

    def get_all_stat(self):
        qs = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .select_related('student').order_by(F('rank_total_psat').asc(nulls_last=True))
        )
        return qs

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        all_stat = self.get_all_stat()
        paginator = Paginator(all_stat, 20)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        student_ids = []
        for obj in page_obj:
            student_ids.append(obj.student.id)

        return page_obj, page_range, student_ids


class IndexViewMixin(ConstantIconSet, AdminBaseMixin):
    sub_title: str
    current_category: str
    category_list: list
    search_student_name: str
    statistics: list
    page_obj: any
    page_range: any
    student_ids: list
    base_url: str
    pagination_url: str

    def get_properties(self):
        super().get_properties()

        self.sub_title = f'제{self.round}회 프라임 모의고사'

        self.current_category = self.get_variable('category') or '전체'
        self.category_list = self.get_category_list()
        self.search_student_name = self.get_variable('student_name')

        self.statistics = self.get_statistics()

        self.page_obj, self.page_range, self.student_ids = self.get_paginator_info()
        self.base_url = reverse_lazy(
            'prime_admin:catalog_year_round', args=[self.year, self.round])
        self.pagination_url = f'{self.base_url}?category={self.current_category}'

    def get_variable(self, variable: str) -> str:
        variable_get = self.request.GET.get(variable, '')
        variable_post = self.request.POST.get(variable, '')
        if variable_get:
            return variable_get
        return variable_post

    def get_category_list(self):
        category_list = ['전체']
        all_category = list(
            self.student_model.objects.filter(year=self.year, round=self.round)
            .order_by('category').values_list('category', flat=True).distinct()
        )
        category_list.extend(all_category)
        return category_list

    def get_all_stat(self):
        qs = (
            self.statistics_model.objects.filter(student__year=self.year, student__round=self.round)
            .order_by('rank_total_psat')
        )
        if self.search_student_name:
            return qs.filter(student__name=self.search_student_name)
        if self.current_category and self.current_category != '전체':
            return qs.filter(student__category=self.current_category)
        return qs

    def get_paginator_info(self) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', 1)
        all_stat = self.get_all_stat()
        paginator = Paginator(all_stat, 20)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

        student_ids = []
        for obj in page_obj:
            student_ids.append(obj.student.id)

        return page_obj, page_range, student_ids


class UpdateAnswerMixin(ConstantIconSet, AdminBaseMixin):
    def update_answer(self):
        filename = self.get_answer_filename()
        answer_correct_dict = self.get_answer_correct_dict(filename)
        for sub, problems in answer_correct_dict.items():
            for problem in problems:
                number = problem['number']
                answer = problem['ans_number']
                with transaction.atomic():
                    try:
                        answer_count = self.answer_count_model.objects.get(
                            category=self.category,
                            year=self.year,
                            ex=self.ex,
                            round=self.round,
                            sub=sub,
                            number=number,
                        )
                    except self.answer_count_model.DoesNotExist:
                        answer_count = self.answer_count_model.objects.create(
                            category=self.category,
                            year=self.year,
                            ex=self.ex,
                            round=self.round,
                            sub=sub,
                            number=number,
                            count_total=0
                        )
                    answer_count.answer = answer
                    answer_count.save()
        return '정답 업데이트를 완료했습니다.'


class UpdateScoreMixin(ConstantIconSet, AdminBaseMixin):
    def update_score(self):
        update_list = []
        create_list = []
        update_count = 0
        create_count = 0
        score_keys = [
            'score_heonbeob', 'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat', 'score_psat_avg',
        ]

        students = self.student_model.objects.filter(
            category=self.category,
            year=self.year,
            ex=self.ex,
            round=self.round,
        )
        for student in students:
            score = self.calculate_score(student)
            try:
                stat = self.statistics_model.objects.get(student=student)
                fields_not_match = any(
                    getattr(stat, key) != score[key] for key in score_keys
                )
                if fields_not_match:
                    for field, value in score.items():
                        setattr(stat, field, value)
                    update_list.append(stat)
                    update_count += 1
            except self.statistics_model.DoesNotExist:
                score['student_id'] = student.id
                create_list.append(self.statistics_model(**score))
                create_count += 1

        try:
            with transaction.atomic():
                if create_list:
                    self.statistics_model.objects.bulk_create(create_list)
                    message = f'총 {create_count}명의 성적 자료가 입력되었습니다.'
                elif update_list:
                    self.statistics_model.objects.bulk_update(update_list, score_keys)
                    message = f'총 {update_count}명의 성적 자료가 업데이트되었습니다.'
                else:
                    message = f'기존에 입력된 성적 자료와 일치합니다.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'업데이트 과정에서 에러가 발생했습니다.'

        return message

    def calculate_score(self, student):
        score_dict = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        if self.ex == '칠급':
            score_dict.pop('헌법')

        filename = self.get_answer_filename()
        answer_correct_dict = self.get_answer_correct_dict(filename)
        for sub in score_dict:
            try:
                answer_student_sub = self.answer_model.objects.get(sub=sub, student=student)
                answer_correct_list = answer_correct_dict[sub]

                correct_count = 0
                for index, problem in enumerate(answer_correct_list):
                    ans_number = problem['ans_number']
                    ans_number_list = problem['ans_number_list']
                    answer_student = getattr(answer_student_sub, f'prob{index + 1}')
                    if answer_student in ans_number_list or ans_number == answer_student:
                        correct_count += 1
                score_dict[sub] = correct_count * 100 / len(answer_correct_list)

            except self.answer_model.DoesNotExist:
                score_dict[sub] = 0

        score_dict['psat'] = sum([score_dict['언어'], score_dict['자료'], score_dict['상황']])
        score_dict['psat_avg'] = score_dict['psat'] / 3

        score_field_dict = {}
        for sub, field in self.sub_field.items():
            score_field_dict[field] = score_dict[sub]

        return score_field_dict


class UpdateStatisticsMixin(ConstantIconSet, AdminBaseMixin):
    rank_annotation_keys = [
        'total_eoneo',
        'total_jaryo',
        'total_sanghwang',
        'total_psat',
        'total_heonbeob',

        'department_eoneo',
        'department_jaryo',
        'department_sanghwang',
        'department_psat',
        'department_heonbeob',

        'ratio_total_eoneo',
        'ratio_total_jaryo',
        'ratio_total_sanghwang',
        'ratio_total_psat',
        'ratio_total_heonbeob',

        'ratio_department_eoneo',
        'ratio_department_jaryo',
        'ratio_department_sanghwang',
        'ratio_department_psat',
        'ratio_department_heonbeob',
    ]

    rank_update_keys = [
        f'rank_{key}' for key in rank_annotation_keys
    ]

    def get_next_url(self):
        return reverse_lazy('predict_admin:detail', args=[self.category, self.year, self.ex, self.round])

    @staticmethod
    def get_rank_list(queryset, rank_type: str):
        def rank_func(field_name) -> Window:
            return Window(expression=Rank(), order_by=F(field_name).desc())

        def rank_ratio_func(field_name) -> Window:
            return Window(expression=PercentRank(), order_by=F(field_name).desc())

        return queryset.annotate(**{
            f'{rank_type}_eoneo': rank_func('score_eoneo'),
            f'{rank_type}_jaryo': rank_func('score_jaryo'),
            f'{rank_type}_sanghwang': rank_func('score_sanghwang'),
            f'{rank_type}_psat': rank_func('score_psat'),
            f'{rank_type}_heonbeob': rank_func('score_heonbeob'),

            f'ratio_{rank_type}_eoneo': rank_ratio_func('score_eoneo'),
            f'ratio_{rank_type}_jaryo': rank_ratio_func('score_jaryo'),
            f'ratio_{rank_type}_sanghwang': rank_ratio_func('score_sanghwang'),
            f'ratio_{rank_type}_psat': rank_ratio_func('score_psat'),
            f'ratio_{rank_type}_heonbeob': rank_ratio_func('score_heonbeob'),
        }).values(
            'student_id', f'{rank_type}_eoneo', f'{rank_type}_jaryo', f'{rank_type}_sanghwang',
            f'{rank_type}_psat', f'{rank_type}_heonbeob',
            f'ratio_{rank_type}_eoneo', f'ratio_{rank_type}_jaryo', f'ratio_{rank_type}_sanghwang',
            f'ratio_{rank_type}_psat', f'ratio_{rank_type}_heonbeob',
        )

    def update_statistics(self):
        update_list = []
        update_count = 0

        statistics_qs_total = self.statistics_model.objects.filter(
            student__category=self.category,
            student__year=self.year,
            student__ex=self.ex,
            student__round=self.round,
        )
        rank_list_total = self.get_rank_list(statistics_qs_total, 'total')

        for stat in statistics_qs_total:
            statistics_qs_department = statistics_qs_total.filter(
                student__department_id=stat.student.department_id)
            rank_list_department = self.get_rank_list(statistics_qs_department, 'department')

            rank_data_dict = {}
            for row in rank_list_total:
                if row['student_id'] == stat.student_id:
                    rank_data_dict.update(row)
            for row in rank_list_department:
                if row['student_id'] == stat.student_id:
                    rank_data_dict.update(row)

            fields_not_match = any(
                getattr(stat, f'rank_{key}') != rank_data_dict[key] for key in self.rank_annotation_keys
            )
            if fields_not_match:
                for field, value in rank_data_dict.items():
                    setattr(stat, f'rank_{field}', value)
                update_list.append(stat)
                update_count += 1

        try:
            with transaction.atomic():
                if update_list:
                    self.statistics_model.objects.bulk_update(update_list, self.rank_update_keys)
                    message = f'총 {update_count}명의 통계 자료가 업데이트되었습니다.'
                else:
                    message = f'기존에 입력된 통계 자료와 일치합니다.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'업데이트 과정에서 에러가 발생했습니다.'

        return message


class ExportStatisticsToExcelMixin(IndexViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()
        statistics = self.get_statistics()

        df = pd.DataFrame.from_records(statistics)
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False, engine='xlsxwriter')

        if self.category == 'PSAT':
            filename = f'{self.year}{self.ex}_성적통계(예측).xlsx'
        else:
            filename = f'{self.year}{self.ex}-{self.round}회_성적통계(예측).xlsx'
        filename = quote(filename)

        response = HttpResponse(
            excel_data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportAnalysisToExcelMixin(DetailViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()

        def get_df(df_target):
            print(df_target)
            df = pd.DataFrame.from_records(df_target)
            df = df.drop('sub', axis=1)
            number = df.pop('number')
            answer_correct = df.pop('answer_correct')
            rate_correct = df.pop('rate_correct')
            answer_predict = df.pop('answer_predict')
            rate_accuracy = df.pop('rate_accuracy')

            df.insert(0, 'number', number)
            df.insert(1, 'answer_correct', answer_correct)
            df.insert(2, 'rate_correct', rate_correct)
            df.insert(3, 'answer_predict', answer_predict)
            df.insert(4, 'rate_accuracy', rate_accuracy)

            return df

        df_heonbeob = get_df(self.answer_count_analysis['헌법'])
        df_eoneo = get_df(self.answer_count_analysis['언어'])
        df_jaryo = get_df(self.answer_count_analysis['자료'])
        df_sanghwang = get_df(self.answer_count_analysis['상황'])

        excel_data = io.BytesIO()
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            df_heonbeob.to_excel(writer, sheet_name='헌법', index=False)
            df_eoneo.to_excel(writer, sheet_name='언어', index=False)
            df_jaryo.to_excel(writer, sheet_name='자료', index=False)
            df_sanghwang.to_excel(writer, sheet_name='상황', index=False)

        if self.category == 'PSAT':
            filename = f'{self.year}{self.ex}_문항분석표(예측).xlsx'
        else:
            filename = f'{self.year}{self.ex}-{self.round}회_문항분석표(예측).xlsx'
        filename = quote(filename)

        response = HttpResponse(
            excel_data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportScoresToExcelMixin(IndexViewMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()

        department_list = self.department_model.objects.values('id', 'name')
        department_dict = {}
        for department in department_list:
            department_id = department['id']
            department_name = department['name']
            department_dict[f'id_{department_id}'] = department_name

        queryset = (
            self.statistics_model.objects.filter(
                student__category=self.category,
                student__year=self.year,
                student__ex=self.ex,
                student__round=self.round
            )
            .annotate(
                이름=F('student__name'), 수험번호=F('student__serial'), department_id=F('student__department_id'),

                헌법_점수=F('score_heonbeob'), 언어_점수=F('score_eoneo'),
                자료_점수=F('score_jaryo'), 상황_점수=F('score_sanghwang'),
                PSAT_총점=F('score_psat'), PSAT_평균=F('score_psat_avg'),

                헌법_전체_석차=F('rank_total_heonbeob'), 언어_전체_석차=F('rank_total_eoneo'),
                자료_전체_석차=F('rank_total_jaryo'), 상황_전체_석차=F('rank_total_sanghwang'),
                PSAT_전체_석차=F('rank_total_psat'),

                헌법_전체_석차_백분율=F('rank_ratio_total_heonbeob'), 언어_전체_석차_백분율=F('rank_ratio_total_eoneo'),
                자료_전체_석차_백분율=F('rank_ratio_total_jaryo'), 상황_전체_석차_백분율=F('rank_ratio_total_sanghwang'),
                PSAT_전체_석차_백분율=F('rank_ratio_total_psat'),

                헌법_직렬_석차=F('rank_department_heonbeob'), 언어_직렬_석차=F('rank_department_eoneo'),
                자료_직렬_석차=F('rank_department_jaryo'), 상황_직렬_석차=F('rank_department_sanghwang'),
                PSAT_직렬_석차=F('rank_department_psat'),

                헌법_직렬_석차_백분율=F('rank_ratio_total_heonbeob'), 언어_직렬_석차_백분율=F('rank_ratio_total_eoneo'),
                자료_직렬_석차_백분율=F('rank_ratio_total_jaryo'), 상황_직렬_석차_백분율=F('rank_ratio_total_sanghwang'),
                PSAT_직렬_석차_백분율=F('rank_ratio_total_psat'),
            )
            .values(
                '이름', '수험번호', 'department_id',
                '헌법_점수', '헌법_전체_석차', '헌법_전체_석차_백분율', '헌법_직렬_석차', '헌법_직렬_석차_백분율',
                '언어_점수', '언어_전체_석차', '언어_전체_석차_백분율', '언어_직렬_석차', '언어_직렬_석차_백분율',
                '자료_점수', '자료_전체_석차', '자료_전체_석차_백분율', '자료_직렬_석차', '자료_직렬_석차_백분율',
                '상황_점수', '상황_전체_석차', '상황_전체_석차_백분율', '상황_직렬_석차', '상황_직렬_석차_백분율',
                'PSAT_총점', 'PSAT_평균', 'PSAT_전체_석차', 'PSAT_전체_석차_백분율', 'PSAT_직렬_석차', 'PSAT_직렬_석차_백분율',
            )
        )

        for query in queryset:
            department_id = query.pop('department_id')
            query['직렬'] = department_dict[f'id_{department_id}']

        df = pd.DataFrame.from_records(queryset)

        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False, engine='xlsxwriter')

        if self.category == 'PSAT':
            filename = f'{self.year}{self.ex}_성적일람표(예측).xlsx'
        else:
            filename = f'{self.year}{self.ex}-{self.round}회_성적일람표(예측).xlsx'
        filename = quote(filename)

        response = HttpResponse(
            excel_data.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response


class ExportTranscriptToPdfViewMixin(IndexViewMixin):
    page_number: int | str

    def post(self, request, *args, **kwargs):
        from score.views.prime_v2.admin_views import IndividualStudentPrintView
        self.get_properties()

        page_number = request.GET.get('page', 1)
        exam_round = self.round

        # Extract parameters from URL
        student_ids = [int(student_id) for student_id in request.POST.get('student_ids').split(',')]

        # Create a zip file to store the individual PDFs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for student_id in student_ids:
                student = self.student_model.objects.get(id=student_id)
                student_name = student.name
                student_serial = student.serial

                html_content = IndividualStudentPrintView.as_view()(
                    request, student_id=student_id, *args, **kwargs).rendered_content

                # Convert HTML to PDF using pdfkit
                options = {
                    '--page-width': '297mm',
                    '--page-height': '210mm',
                }
                pdf_file_path = f"제{exam_round}회_전국모의고사_{student_id}_{student_serial}_{student_name}.pdf"
                pdf_content = pdfkit.from_string(html_content, False, options=options)

                # Add the PDF to the zip file
                zip_file.writestr(pdf_file_path, pdf_content)

        filename = f'제{exam_round}회_전국모의고사_성적표_모음_{page_number}.zip'
        filename = quote(filename)

        # Create a response with the zipped content
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        return response


class ExportPredictDataToGoogleSheetMixin(ConstantIconSet, AdminBaseMixin):
    def export_data(self):
        # Load credentials from JSON file
        base_dir = settings.BASE_DIR
        google_key_json = f'{base_dir}/google_key.json'
        google_sheet_json = f'{base_dir}/google_sheet.json'
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(google_key_json, scope)
        gc = gspread.authorize(credentials)

        with open(google_sheet_json, "r") as config_file:
            config = json.load(config_file)

        student_serializer = serializers.PredictStudentSerializer(
            self.student_model.objects.all(), many=True)
        answer_serializer = serializers.PredictAnswerSerializer(
            self.answer_model.objects.all(), many=True)
        answer_count_serializer = serializers.PredictAnswerCountSerializer(
            self.answer_count_model.objects.all(), many=True)
        statistics_serializer = serializers.PredictStatisticsSerializer(
            self.statistics_model.objects.all(), many=True)

        data_student = student_serializer.data
        data_answer = answer_serializer.data
        data_answer_count = answer_count_serializer.data
        data_statistics = statistics_serializer.data

        df_student = pd.DataFrame(data_student)
        df_answer = pd.DataFrame(data_answer)
        df_answer_count = pd.DataFrame(data_answer_count)
        df_statistics = pd.DataFrame(data_statistics)

        sheet_key_predict = config["sheet_key_predict"]
        workbook = gc.open_by_key(sheet_key_predict)

        worksheet_student = workbook.worksheet('student')
        worksheet_answer = workbook.worksheet('answer')
        worksheet_answer_count = workbook.worksheet('answer_count')
        worksheet_statistics = workbook.worksheet('statistics')

        worksheet_student.clear()
        worksheet_answer.clear()
        worksheet_answer_count.clear()
        worksheet_statistics.clear()

        worksheet_student.update(
            [df_student.columns.values.tolist()] + df_student.values.tolist()
        )
        worksheet_answer.update(
            [df_answer.columns.values.tolist()] + df_answer.values.tolist()
        )
        worksheet_answer_count.update(
            [df_answer_count.columns.values.tolist()] + df_answer_count.values.tolist()
        )
        worksheet_statistics.update(
            [df_statistics.columns.values.tolist()] + df_statistics.values.tolist()
        )
