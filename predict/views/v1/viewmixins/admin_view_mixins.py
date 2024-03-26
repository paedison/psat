import io
import json
import traceback
from urllib.parse import quote

import django.db.utils
import gspread
import pandas as pd
from django.conf import settings
from django.db import transaction
from django.db.models import F, Window
from django.db.models.functions import Rank, PercentRank
from django.http import HttpResponse
from django.urls import reverse_lazy
from oauth2client.service_account import ServiceAccountCredentials

from common.constants.icon_set import ConstantIconSet
from common.models import User
from predict import serializers
from predict.views.v1.utils import get_dict_by_sub
from .base_mixins import AdminBaseMixin


class ListViewMixin(AdminBaseMixin, ConstantIconSet):

    @staticmethod
    def get_url(name):
        base_url = reverse_lazy(f'predict_test_admin:{name}')
        return f'{base_url}?'

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


class DetailViewMixin(AdminBaseMixin, ConstantIconSet):

    def get_url(self, name):
        base_url = reverse_lazy(
            f'predict_test_admin:{name}', args=[self.category, self.year, self.ex, self.round])
        return f'{base_url}?'

    def get_sub_title(self):
        if self.category == 'Prime':
            return f'제{self.round}회 {self.exam.exam} 성적 예측'
        return f'{self.year}년 {self.exam.exam} 성적 예측'

    def get_sub_answer_count(self, sub: str):
        field_keys = [
            'number',
            'count_total', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0',
            'rate_1', 'rate_2', 'rate_3', 'rate_4', 'rate_5', 'rate_0', 'rate_None'
        ]

        def get_answer_count(model):
            return model.objects.filter(exam=self.exam, sub=sub).order_by('number').values(*field_keys)

        answer_count = list(get_answer_count(self.answer_count_model))
        answer_count_top_rank = list(get_answer_count(self.answer_count_top_rank_model))
        answer_count_middle_rank = list(get_answer_count(self.answer_count_middle_rank_model))
        answer_count_low_rank = list(get_answer_count(self.answer_count_low_rank_model))
        answer_correct_dict = self.get_answer_correct_dict()

        page_obj_total, page_range_total = self.get_paginator_info(answer_count)
        page_obj_top, page_range_top = self.get_paginator_info(answer_count_top_rank)
        page_obj_middle, page_range_middle = self.get_paginator_info(answer_count_middle_rank)
        page_obj_low, page_range_low = self.get_paginator_info(answer_count_low_rank)

        for index, problem in enumerate(page_obj_total):
            number = problem['number']  # 문제 번호
            ans_number_correct = answer_correct_dict[sub][number - 1]['ans_number']

            problem_top_rank = page_obj_top[index]
            problem_middle_rank = page_obj_middle[index]
            problem_low_rank = page_obj_low[index]

            if ans_number_correct in range(1, 6):
                rate_correct = problem[f'rate_{ans_number_correct}']
                rate_correct_top_rank = problem_top_rank[f'rate_{ans_number_correct}']
                rate_correct_middle_rank = problem_middle_rank[f'rate_{ans_number_correct}']
                rate_correct_low_rank = problem_low_rank[f'rate_{ans_number_correct}']
            else:
                answer_correct_list = [int(digit) for digit in str(ans_number_correct)]
                try:
                    rate_correct = sum(problem[f'rate_{ans}'] for ans in answer_correct_list)
                    rate_correct_top_rank = sum(problem_top_rank[f'rate_{ans}'] for ans in answer_correct_list)
                    rate_correct_middle_rank = sum(problem_middle_rank[f'rate_{ans}'] for ans in answer_correct_list)
                    rate_correct_low_rank = sum(problem_low_rank[f'rate_{ans}'] for ans in answer_correct_list)
                except TypeError:
                    rate_correct = 0
                    rate_correct_top_rank = 0
                    rate_correct_middle_rank = 0
                    rate_correct_low_rank = 0
            problem['answer_correct'] = ans_number_correct

            problem['rate_correct'] = rate_correct
            problem['rate_correct_top_rank'] = rate_correct_top_rank
            problem['rate_correct_middle_rank'] = rate_correct_middle_rank
            problem['rate_correct_low_rank'] = rate_correct_low_rank

            answer_count_list = []  # list for counting answers
            for i in range(5):
                ans_number = i + 1
                answer_count_list.append(problem[f'count_{ans_number}'])
            ans_number_predict = answer_count_list.index(max(answer_count_list)) + 1  # 예상 정답
            rate_accuracy = problem[f'rate_{ans_number_predict}']  # 정확도
            problem['answer_predict'] = ans_number_predict
            problem['rate_accuracy'] = rate_accuracy

            for field in field_keys:
                if field != 'sub' and field != 'number':
                    problem[f'top_rank_{field}'] = problem_top_rank[field]
                    problem[f'middle_rank_{field}'] = problem_middle_rank[field]
                    problem[f'low_rank_{field}'] = problem_low_rank[field]

        return page_obj_total, page_range_total

    def get_all_stat(self, model_type=None):
        field_keys_score = [
            'id', 'student_id',
            'score_heonbeob', 'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat', 'score_psat_avg',
        ]
        field_keys_rank = [
            'rank_total_heonbeob', 'rank_total_eoneo', 'rank_total_jaryo',
            'rank_total_sanghwang', 'rank_total_psat',
            'rank_department_heonbeob', 'rank_department_eoneo', 'rank_department_jaryo',
            'rank_department_sanghwang', 'rank_department_psat',
            'rank_ratio_total_heonbeob', 'rank_ratio_total_eoneo', 'rank_ratio_total_jaryo',
            'rank_ratio_total_sanghwang', 'rank_ratio_total_psat',
            'rank_ratio_department_heonbeob', 'rank_ratio_department_eoneo', 'rank_ratio_department_jaryo',
            'rank_ratio_department_sanghwang', 'rank_ratio_department_psat',
        ]
        if model_type == 'virtual':
            stat_list = (
                self.statistics_virtual_model.objects.filter(student__exam=self.exam)
                .order_by(F('rank_total_psat').asc(nulls_last=True))
                .values(
                    *field_keys_score,
                    user_id=F('student__user_id'),
                    name=F('student__name'),
                    serial=F('student__serial'),
                    department_id=F('student__department_id'),
                )
            )
        else:
            stat_list = (
                self.statistics_model.objects.filter(student__exam=self.exam)
                .order_by(F('rank_total_psat').asc(nulls_last=True))
                .values(
                    *field_keys_score,
                    *field_keys_rank,
                    user_id=F('student__user_id'),
                    name=F('student__name'),
                    serial=F('student__serial'),
                    department_id=F('student__department_id'),
                )
            )
        for stat in stat_list:
            unit_name = ''
            department_name = ''
            username = ''
            for d in self.department_list:
                if d['id'] == stat['department_id']:
                    unit_name = d['unit_name']
                    department_name = d['name']
            for u in self.user_list:
                if u['id'] == stat['user_id']:
                    username = u['username']
            stat['unit_name'] = unit_name
            stat['department_name'] = department_name
            stat['username'] = username
        return stat_list


class UpdateAnswerMixin(AdminBaseMixin, ConstantIconSet):
    def update_answer(self):
        update_list = []
        create_list = []
        update_count = 0
        create_count = 0
        update_keys = ['answer']
        message = '기존에 입력된 정답 데이터와 일치합니다.'

        answer_correct_dict = self.get_answer_correct_dict()
        for sub, problems in answer_correct_dict.items():
            for problem in problems:
                number = problem['number']
                ans_number = problem['ans_number']
                try:
                    answer_count = self.answer_count_model.objects.get(
                        exam__category=self.category,
                        exam__year=self.year,
                        exam__ex=self.ex,
                        exam__round=self.round,
                        sub=sub,
                        number=number,
                    )
                    if answer_count.answer != ans_number:
                        answer_count.answer = ans_number
                        update_list.append(answer_count)
                        update_count += 1
                except self.answer_count_model.DoesNotExist:
                    answer_count = self.answer_count_model.objects.create(
                        exam__category=self.category,
                        exam__year=self.year,
                        exam__ex=self.ex,
                        exam__round=self.round,
                        sub=sub,
                        number=number,
                        count_total=0
                    )
                    answer_count.answer = ans_number
                    create_list.append(answer_count)
                    create_count += 1
        try:
            with transaction.atomic():
                if create_list:
                    self.answer_count_model.objects.bulk_create(create_list)
                    message = f'{create_count}개의 문제 정답을 새로 기록했습니다.'
                elif update_list:
                    self.answer_count_model.objects.bulk_update(update_list, update_keys)
                    message = f'{update_count}개의 문제 정답을 업데이트했습니다.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'업데이트 과정에서 에러가 발생했습니다.'

        return message


class UpdateScoreMixin(AdminBaseMixin, ConstantIconSet):
    def update_score(self):
        update_list = []
        create_list = []
        update_count = 0
        create_count = 0
        update_keys = [
            'score_heonbeob', 'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat', 'score_psat_avg',
        ]
        message = '기존에 입력된 성적 데이터와 일치합니다.'

        students = self.student_model.objects.filter(
            exam__category=self.category,
            exam__year=self.year,
            exam__ex=self.ex,
            exam__round=self.round,
        )
        for student in students:
            score = self.calculate_score(student)
            try:
                stat = self.statistics_model.objects.get(student=student)
                fields_not_match = any(
                    getattr(stat, key) != score[key] for key in update_keys
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
                    message = f'총 {create_count}명의 성적 데이터가 입력되었습니다.'
                elif update_list:
                    self.statistics_model.objects.bulk_update(update_list, update_keys)
                    message = f'총 {update_count}명의 성적 데이터가 업데이트되었습니다.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'업데이트 과정에서 에러가 발생했습니다.'

        return message

    def calculate_score(self, student):
        score_dict = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        if self.ex == '칠급':
            score_dict.pop('헌법')

        answer_correct_dict = self.get_answer_correct_dict()
        for sub in score_dict:
            try:
                answer_student_sub = self.answer_model.objects.get(sub=sub, student=student, is_confirmed=True)
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


class UpdateStatisticsMixin(AdminBaseMixin, ConstantIconSet):
    annotation_keys = [
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

    update_keys = [
        f'rank_{key}' for key in annotation_keys
    ]

    def get_next_url(self):
        return reverse_lazy('predict_test_admin:detail', args=[self.category, self.year, self.ex, self.round])

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
        message = f'기존에 입력된 통계 데이터와 일치합니다.'

        statistics_qs_total = self.statistics_model.objects.filter(
            student__exam__category=self.category,
            student__exam__year=self.year,
            student__exam__ex=self.ex,
            student__exam__round=self.round,
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
                getattr(stat, f'rank_{key}') != rank_data_dict[key] for key in self.annotation_keys
            )
            if fields_not_match:
                for field, value in rank_data_dict.items():
                    setattr(stat, f'rank_{field}', value)
                update_list.append(stat)
                update_count += 1

        try:
            with transaction.atomic():
                if update_list:
                    self.statistics_model.objects.bulk_update(update_list, self.update_keys)
                    message = f'총 {update_count}명의 통계 데이터가 업데이트되었습니다.'
        except django.db.utils.IntegrityError:
            traceback_message = traceback.format_exc()
            print(traceback_message)
            message = f'업데이트 과정에서 에러가 발생했습니다.'

        return message


class ExportStatisticsToExcelMixin(AdminBaseMixin):
    def get(self, request, *args, **kwargs):
        self.get_properties()
        statistics = self.get_excel_statistics()

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
    def get_answer_count_analysis(self):
        field_keys = [
            'sub', 'number',
            'count_total', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_0',
            'rate_1', 'rate_2', 'rate_3', 'rate_4', 'rate_5', 'rate_0', 'rate_None'
        ]

        def get_answer_count(model):
            return model.objects.filter(exam=self.exam).order_by('sub', 'number').values(*field_keys)

        answer_count = list(get_answer_count(self.answer_count_model))
        answer_count_top_rank = list(get_answer_count(self.answer_count_top_rank_model))
        answer_count_middle_rank = list(get_answer_count(self.answer_count_middle_rank_model))
        answer_count_low_rank = list(get_answer_count(self.answer_count_low_rank_model))

        answer_correct_dict = self.get_answer_correct_dict()

        for index, problem in enumerate(answer_count):
            sub = problem['sub']  # 과목
            number = problem['number']  # 문제 번호
            ans_number_correct = answer_correct_dict[sub][number - 1]['ans_number']

            problem_top_rank = answer_count_top_rank[index]
            problem_middle_rank = answer_count_middle_rank[index]
            problem_low_rank = answer_count_low_rank[index]

            if ans_number_correct in range(1, 6):
                rate_correct = problem[f'rate_{ans_number_correct}']
                rate_correct_top_rank = problem_top_rank[f'rate_{ans_number_correct}']
                rate_correct_middle_rank = problem_middle_rank[f'rate_{ans_number_correct}']
                rate_correct_low_rank = problem_low_rank[f'rate_{ans_number_correct}']
            else:
                answer_correct_list = [int(digit) for digit in str(ans_number_correct)]
                try:
                    rate_correct = sum(problem[f'rate_{ans}'] for ans in answer_correct_list)
                    rate_correct_top_rank = sum(problem_top_rank[f'rate_{ans}'] for ans in answer_correct_list)
                    rate_correct_middle_rank = sum(problem_middle_rank[f'rate_{ans}'] for ans in answer_correct_list)
                    rate_correct_low_rank = sum(problem_low_rank[f'rate_{ans}'] for ans in answer_correct_list)
                except TypeError:
                    rate_correct = 0
                    rate_correct_top_rank = 0
                    rate_correct_middle_rank = 0
                    rate_correct_low_rank = 0
            problem['answer_correct'] = ans_number_correct

            problem['rate_correct'] = rate_correct
            problem['rate_correct_top_rank'] = rate_correct_top_rank
            problem['rate_correct_middle_rank'] = rate_correct_middle_rank
            problem['rate_correct_low_rank'] = rate_correct_low_rank

            answer_count_list = []  # list for counting answers
            for i in range(5):
                ans_number = i + 1
                answer_count_list.append(problem[f'count_{ans_number}'])
            ans_number_predict = answer_count_list.index(max(answer_count_list)) + 1  # 예상 정답
            rate_accuracy = problem[f'rate_{ans_number_predict}']  # 정확도
            problem['answer_predict'] = ans_number_predict
            problem['rate_accuracy'] = rate_accuracy

            for field in field_keys:
                if field != 'sub' and field != 'number':
                    problem[f'top_rank_{field}'] = problem_top_rank[field]
                    problem[f'middle_rank_{field}'] = problem_middle_rank[field]
                    problem[f'low_rank_{field}'] = problem_low_rank[field]

        return get_dict_by_sub(answer_count)

    def get(self, request, *args, **kwargs):
        self.get_properties()

        def get_df(df_target):
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

        answer_count_analysis = self.get_answer_count_analysis()
        df_heonbeob = get_df(answer_count_analysis['헌법'])
        df_eoneo = get_df(answer_count_analysis['언어'])
        df_jaryo = get_df(answer_count_analysis['자료'])
        df_sanghwang = get_df(answer_count_analysis['상황'])

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


class ExportScoresToExcelMixin(AdminBaseMixin):
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
                student__exam__category=self.category,
                student__exam__year=self.year,
                student__exam__ex=self.ex,
                student__exam__round=self.round
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


class ExportPredictDataToGoogleSheetMixin(AdminBaseMixin, ConstantIconSet):
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
        answer_count_top_rank_serializer = serializers.PredictAnswerCountTopRankSerializer(
            self.answer_count_top_rank_model.objects.all(), many=True)
        statistics_serializer = serializers.PredictStatisticsSerializer(
            self.statistics_model.objects.all(), many=True)

        data_student = student_serializer.data
        data_answer = answer_serializer.data
        data_answer_count = answer_count_serializer.data
        data_answer_count_top_rank = answer_count_top_rank_serializer.data
        data_statistics = statistics_serializer.data

        df_student = pd.DataFrame(data_student)
        df_answer = pd.DataFrame(data_answer)
        df_answer_count = pd.DataFrame(data_answer_count)
        df_answer_count_top_rank = pd.DataFrame(data_answer_count_top_rank)
        df_statistics = pd.DataFrame(data_statistics)

        sheet_key_predict = config["sheet_key_predict"]
        workbook = gc.open_by_key(sheet_key_predict)

        worksheet_student = workbook.worksheet('student')
        worksheet_answer = workbook.worksheet('answer')
        worksheet_answer_count = workbook.worksheet('answer_count')
        worksheet_answer_count_top_rank = workbook.worksheet('answer_count_top_rank')
        worksheet_statistics = workbook.worksheet('statistics')

        worksheet_student.clear()
        worksheet_answer.clear()
        worksheet_answer_count.clear()
        worksheet_answer_count_top_rank.clear()
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
        worksheet_answer_count_top_rank.update(
            [df_answer_count_top_rank.columns.values.tolist()] + df_answer_count_top_rank.values.tolist()
        )
        worksheet_statistics.update(
            [df_statistics.columns.values.tolist()] + df_statistics.values.tolist()
        )
