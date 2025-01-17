import dataclasses
import json
from typing import Type

from django.db import transaction
from django.db.models import QuerySet, F
from django.urls import reverse

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest
from .. import forms, models


@dataclasses.dataclass
class PredictExamVars:
    request: HtmxHttpRequest | None
    psat_year: int
    psat_exam: str

    # common vars
    default_count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    extra_count_fields = ['count_multiple', 'count_total']
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']
    subject_to_field_dict = {
        '언어논리': 'eoneo', '자료해석': 'jaryo', '상황판단': 'sanghwang',
        '헌법': 'heonbeob',
    }
    field_to_subject_dict = {
        'eoneo': '언어논리', 'jaryo': '자료해석', 'sanghwang': '상황판단',
        'heonbeob': '헌법',
    }
    subject_vars = {
        '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
        '헌법': ('헌법', 'heonbeob'),
    }
    field_vars = {
        'eoneo': ('언어', '언어논리'), 'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'), 'psat_avg': ('평균', 'PSAT 평균'),
        'heonbeob': ('헌법', '헌법'),
    }

    info = {'menu': 'predict', 'view_type': 'predict'}
    icon_menu = icon_set_new.ICON_MENU['predict']
    score_template_table_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
    score_template_table_2 = 'a_predict/snippets/index_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
        'prefix_all': ['my', 'total', 'department']
    }

    # psat/police vars
    only_psat_fields = ['eoneo', 'jaryo', 'sanghwang']
    police_common_fields = ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']

    # models
    psat_model = models.PredictPsat
    category_model = models.PredictCategory
    student_model = models.PredictStudent
    answer_model = models.PredictAnswer
    answer_count_model = models.PredictAnswerCount
    score_model = models.PredictScore
    rank_total_model = models.PredictRankTotal
    rank_category_model = models.PredictRankCategory
    location_model = models.PredictLocation

    ##################
    # Forms
    @property
    def student_form(self):
        return forms.PsatStudentForm

    ##################
    # Information Dictionary
    @property
    def psat_info(self) -> dict:
        return {'year': self.psat_year, 'exam': self.psat_exam}

    def get_problem_info(self, field: str, number: int) -> dict:
        return dict(self.psat_info, **{'subject': field, 'number': number})

    @property
    def student_exam_info(self) -> dict:
        return {'student__psat__year': self.psat_year, 'student__psat__exam': self.psat_exam}

    @property
    def exam_url_kwargs(self) -> dict:
        return {'psat_year': self.psat_year, 'psat_exam': self.psat_exam}

    @property
    def department_dict(self) -> dict:
        qs_department = self.category_model.objects.filter(exam=self.psat_exam).order_by('order')
        return {department.name: department.id for department in qs_department}

    ##################
    # Subject Name
    @property
    def sub_list(self) -> list[str]:
        if self.psat_exam == '칠급':
            return ['언어', '상황', '자료']
        return ['헌법', '언어', '자료', '상황']

    @property
    def admin_sub_list(self) -> list[str]:
        return self.sub_list

    @property
    def subject_list(self) -> list[str]:
        if self.psat_exam == '칠급':
            return ['언어논리', '상황판단', '자료해석']
        return ['헌법', '언어논리', '자료해석', '상황판단']

    @property
    def admin_subject_list(self) -> list[str]:
        return ['PSAT'] + self.subject_list

    ##################
    # Subject Field
    @property
    def answer_fields(self) -> list[str]:
        if self.psat_exam == '칠급':
            return ['eoneo', 'sanghwang', 'jaryo']
        return ['heonbeob'] + self.only_psat_fields

    @property
    def all_subject_fields(self) -> list[str]:
        return self.answer_fields

    @property
    def final_field(self) -> str:
        return 'psat_avg'

    @property
    def score_fields(self) -> list[str]:
        return self.answer_fields + [self.final_field]

    @property
    def admin_score_fields(self) -> list[str]:
        return self.score_fields

    def get_subject_field(self, subject) -> str:
        for fld, sub_tuple in self.field_vars.items():
            if fld == subject or sub_tuple[0] == subject or sub_tuple[1] == subject:
                return fld

    def get_field_idx(self, field, admin=False) -> int:
        if admin:
            return self.admin_score_fields.index(field)
        return self.score_fields.index(field)

    ##################
    # Problem Count
    @property
    def problem_count(self) -> dict[str, int]:
        if self.psat_exam == '칠급':
            return {'eoneo': 25, 'jaryo': 25, 'sanghwang': 25}
        return {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}

    @property
    def count_fields(self) -> list[str]:
        return ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5']

    @property
    def all_count_fields(self) -> list[str]:
        return self.count_fields + ['count_multiple', 'count_total']

    ##################
    # URLs
    @property
    def url_index(self) -> str:
        return reverse('predict:index')

    @property
    def url_detail(self) -> str:
        return reverse('predict:detail', kwargs=self.exam_url_kwargs)

    @property
    def url_student_create(self) -> str:
        return reverse('predict:student-create', kwargs=self.exam_url_kwargs)

    @property
    def url_answer_input_list(self) -> list[str]:
        kwargs_dict = [dict(self.exam_url_kwargs, **{'subject_field': fld}) for fld in self.answer_fields]
        return [reverse('predict:answer-input', kwargs=kwargs) for kwargs in kwargs_dict]

    def get_url_answer_input(self, subject_field) -> str:
        if subject_field in self.answer_fields:
            kwargs = dict(self.exam_url_kwargs, **{'subject_field': subject_field})
            return reverse('predict:answer-input', kwargs=kwargs)

    def get_url_answer_confirm(self, subject_field) -> str:
        kwargs = dict(self.exam_url_kwargs, **{'subject_field': subject_field})
        return reverse('predict:answer-confirm', kwargs=kwargs)

    @property
    def url_admin_list(self) -> str:
        return reverse('predict:admin-list')

    @property
    def url_admin_detail(self) -> str:
        return reverse('predict:admin-detail', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_update(self) -> str:
        return reverse('predict:admin-update', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_export_statistics(self) -> str:
        return reverse('predict:admin-export-statistics', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_export_catalog(self) -> str:
        return reverse('predict:admin-export-catalog', kwargs=self.exam_url_kwargs)

    @property
    def url_admin_export_answer(self) -> str:
        return reverse('predict:admin-export-answer', kwargs=self.exam_url_kwargs)

    ##################
    # Template Contexts
    @property
    def sub_title(self) -> str:
        default = {
            '행시': f'{self.psat_year}년 5급공채 등 합격 예측',
            '칠급': f'{self.psat_year}년 7급공채 등 합격 예측',
        }
        return default[self.psat_exam]

    @property
    def icon_subject(self) -> list[str]:
        return [icon_set_new.ICON_SUBJECT[sub] for sub in self.sub_list]

    @property
    def admin_icon_subject(self) -> list[str]:
        return [icon_set_new.ICON_SUBJECT[sub] for sub in self.sub_list]

    @property
    def info_tab(self) -> dict[str, str]:
        return {'id': ''.join([str(i) for i in range(len(self.score_fields))])}

    @property
    def answer_tab(self) -> dict[str, str]:
        return {'id': ''.join([str(i) for i in range(len(self.sub_list))])}

    @property
    def admin_stat_tab(self) -> dict[str, str]:
        return {'id': ''.join([str(i) for i in range(len(self.admin_subject_list))])}

    @property
    def admin_answer_tab(self) -> dict[str, str]:
        return {'id': ''.join([str(i) for i in range(len(self.admin_sub_list))])}

    ##################
    # Queryset
    def get_psat(self):
        return self.psat_model.objects.filter(**self.psat_info).first()

    def get_all_units(self) -> list[str]:
        return self.category_model.objects.filter(exam=self.psat_exam).values_list('unit', flat=True).unique()

    def get_qs_department(self, unit=None) -> QuerySet:
        if unit:
            return self.category_model.objects.filter(exam=self.psat_exam, unit=unit).order_by('order')
        return self.category_model.objects.filter(exam=self.psat_exam).order_by('order')

    def get_qs_student(self) -> QuerySet:
        return self.student_model.objects.filter(**self.psat_info)

    def get_student(self):
        if self.request.user.is_authenticated:
            return self.student_model.objects.filter(**self.psat_info, user=self.request.user).first()

    def get_location(self, student):
        if self.location_model:
            serial = int(student.serial)
            return self.location_model.objects.filter(
                **self.psat_info, serial_start__lte=serial, serial_end__gte=serial).first()

    def get_qs_answer_count(self) -> QuerySet:
        return self.answer_count_model.objects.filter(**self.psat_info).annotate(
            no=F('number')).order_by('subject', 'number')

    ##################
    # Methods
    def get_score_unit(self, field) -> float | int:
        if self.psat_exam == '칠급' or field in ['heonbeob', '헌법']:
            return 4
        return 2.5

    def get_data_answer_official(self, exam) -> tuple[list[list[dict[str, int | str]]], bool]:
        # {
        #     'heonbeob': [
        #         {
        #             'no': 10,
        #             'ans': 1,
        #         },
        #         ...
        #     ]
        # }
        official_answer_uploaded = False
        data_answer_official: list[list[dict[str, int | str]]] = [
            [
                {'no': idx + 1, 'ans': 0, 'field': fld} for idx in range(cnt)
            ] for fld, cnt in self.problem_count.items()
        ]
        if exam and exam.is_answer_official_opened:
            official_answer_uploaded = True
            try:
                for field, answer in exam.answer_official.items():
                    field_idx = self.get_field_idx(field, admin=True)
                    for no, ans in enumerate(answer, start=1):
                        data_answer_official[field_idx][no - 1] = {'no': no, 'ans': ans, 'field': field}
            except IndexError:
                official_answer_uploaded = False
            except KeyError:
                official_answer_uploaded = False
        return data_answer_official, official_answer_uploaded

    def get_data_answer_predict(self, qs_answer_count) -> list[list[dict[str, int | str]]]:
        data_answer_predict: list[list[dict[str, int | str]]] = [
            [
                {'no': idx + 1, 'ans': 0, 'field': fld} for idx in range(cnt)
            ] for fld, cnt in self.problem_count.items()
        ]
        for answer_count in qs_answer_count:
            fld = answer_count.subject
            if fld in self.all_subject_fields:
                field_idx = self.all_subject_fields.index(fld)
                no = answer_count.number

                count_list = [getattr(answer_count, c) for c in self.count_fields]
                ans_predict = count_list[1:].index(max(count_list[1:])) + 1
                rate_accuracy = round(getattr(answer_count, f'rate_{ans_predict}'), 1)

                count_list.extend([answer_count.count_multiple, answer_count.count_total])

                data_answer_predict[field_idx][no - 1].update({
                    'no': no, 'ans': ans_predict, 'field': fld,
                    'rate_accuracy': rate_accuracy, 'count': count_list,
                })

        return data_answer_predict

    def get_data_answer_student(
            self, student, data_answer_predict, data_answer_official_tuple: tuple
    ) -> list[list[dict[str, int | str]]]:
        data_answer_student: list[list[dict[str, int | str]]] = [
            [
                {'no': idx + 1, 'ans': 0, 'field': fld} for idx in range(self.problem_count[fld])
            ] for fld in self.answer_fields
        ]
        official_answer_uploaded = data_answer_official_tuple[1]

        for dt in student.data:
            fld = dt[0]
            fld_idx = self.get_field_idx(fld)
            is_confirmed = dt[1]
            answer_student = dt[-1]
            if is_confirmed:
                for no_idx, ans_student in enumerate(answer_student):
                    answer_predict = data_answer_predict[fld_idx][no_idx]
                    ans_predict = answer_predict['ans']
                    count_total = answer_predict['count'][-1]
                    result_predict = ans_student == ans_predict

                    rate_selection = 0
                    if count_total:
                        rate_selection = round(answer_predict['count'][ans_student] * 100 / count_total, 1)

                    prediction_is_correct = result_real = None
                    if official_answer_uploaded:
                        answer_official = data_answer_official_tuple[0][fld_idx][no_idx]
                        ans_official = answer_official['ans']
                        prediction_is_correct = ans_official == ans_predict
                        if count_total:
                            if 1 <= ans_official <= 5:
                                result_real = ans_student == ans_official
                                rate_correct = round(
                                    answer_predict['count'][ans_official] * 100 / count_total, 1)
                            else:
                                ans_official_list = [int(ans) for ans in str(ans_official)]
                                result_real = ans_student in ans_official_list
                                rate_correct = round(sum(
                                    answer_predict['count'][ans] for ans in ans_official_list
                                ) * 100 / count_total, 1)
                            answer_official['rate_correct'] = rate_correct

                    answer_predict['prediction_is_correct'] = prediction_is_correct

                    data_answer_student[fld_idx][no_idx].update({
                        'ans': ans_student,
                        'result_predict': result_predict,
                        'rate_selection': rate_selection,
                        'result_real': result_real,
                    })
        return data_answer_student

    def get_info_answer_student(self, exam, student, data_answer_student) -> list[dict]:
        info_answer_student: list[dict[str, int | float | bool | str]] = [
            {
                'field': fld,
                'sub': self.field_vars[fld][0],
                'subject': self.field_vars[fld][1],
                'icon': icon_set_new.ICON_SUBJECT[self.field_vars[fld][0]],
                'participants': exam.participants['all']['total'].get(fld, 0),
                'is_confirmed': False, 'url_answer_input': '',
                'score_real': 0, 'score_predict': 0,
                'problem_count': 0, 'answer_count': 0,
            } for fld in self.score_fields
        ]

        empty_answer_data: list[list[int]] = [
            [0 for _ in range(self.problem_count[fld])] for fld in self.answer_fields
        ]
        answer_input = json.loads(self.request.COOKIES.get('answer_input', '{}')) or empty_answer_data

        score_predict_sum = 0
        score_real_sum = 0
        answer_cnt_sum = 0
        for fld_idx, fld in enumerate(self.score_fields):
            is_confirmed = student.data[fld_idx][1]
            answer_saved = student.data[fld_idx][-1]

            if fld != self.final_field:
                answer_saved_cnt = len([x for x in answer_saved if x != 0])
                answer_input_cnt = len([x for x in answer_input[fld_idx] if x != 0])
                answer_count = max(answer_saved_cnt, answer_input_cnt)
                answer_cnt_sum += answer_count

                correct_predict_count = correct_real_count = 0
                for answer_student in data_answer_student[fld_idx]:
                    result_predict = result_real = False
                    if 'result_predict' in answer_student:
                        result_predict = answer_student['result_predict']
                    if 'result_predict' in answer_student:
                        result_real = answer_student['result_real']
                    correct_predict_count += 1 if result_predict else 0
                    if is_confirmed:
                        correct_real_count += 1 if result_real else 0

                problem_count = self.problem_count[fld]
                score_unit = self.get_score_unit(fld)
                score_real = correct_real_count * score_unit
                score_predict = correct_predict_count * score_unit
                score_real_sum += score_real
                score_predict_sum += score_predict
            else:
                problem_count = sum([
                    self.problem_count[fld] for fld in self.answer_fields
                ])
                answer_count = answer_cnt_sum

                score_real = round(score_real_sum / 3, 1)
                score_predict = round(score_predict_sum / 3, 1)

            url_answer_input = self.get_url_answer_input(fld)
            info_answer_student[fld_idx].update({
                'problem_count': problem_count, 'answer_count': answer_count,
                'score_real': score_real, 'score_predict': score_predict,
                'is_confirmed': is_confirmed, 'url_answer_input': url_answer_input,
            })
        return info_answer_student

    def get_stat_data(
            self, exam, qs_student, student, stat_type: str, filtered: bool = False) -> list[dict[str, int | str]]:
        score_list = {fld: [] for fld in self.score_fields}
        stat_data: list[dict[str, int | float | str | None]] = []
        for fld_idx, fld in enumerate(self.score_fields):
            sub, subject = self.field_vars[fld]
            stat_data.append({
                'field': fld, 'sub': sub, 'subject': subject,
                'icon': icon_set_new.ICON_SUBJECT[sub],
                'is_confirmed': student.data[fld_idx][1],
                'rank': 0, 'score': 0, 'participants': 0,
                'max_score': 0, 'top_score_10': 0,
                'top_score_20': 0, 'avg_score': 0,
                'url_answer_input': '',
            })

        filter_exp = {}
        if stat_type == 'department':
            filter_exp['department'] = student.department
        if filtered:
            filter_exp['answer_all_confirmed_at__lte'] = exam.answer_official_opened_at

        student_score_dict: dict[int, dict[str, int | float]] = {}
        for stu in qs_student:
            student_score_dict[stu.id] = {}
            for dt in stu.data:
                fld = dt[0]
                is_confirmed = dt[1]
                score = dt[2]
                if is_confirmed and fld in score_list:
                    score_list[fld].append(score)
                    student_score_dict[stu.id][fld] = score

        for fld_idx, fld in enumerate(self.score_fields):
            if score_list[fld]:
                student_score = student_score_dict[student.id][fld]
                participants = len(score_list[fld])
                sorted_scores = sorted(score_list[fld], reverse=True)
                try:
                    rank = sorted_scores.index(student_score) + 1
                    max_score = round(sorted_scores[0], 1)
                    top_10_threshold = max(1, int(participants * 0.1))
                    top_20_threshold = max(1, int(participants * 0.2))
                    top_score_10 = round(sorted_scores[top_10_threshold - 1], 1)
                    top_score_20 = round(sorted_scores[top_20_threshold - 1], 1)
                    avg_score = round(sum(score_list[fld]) / participants if participants else 0, 1)
                except ValueError:
                    rank = max_score = top_score_10 = top_score_20 = avg_score = None

                stat_data[fld_idx].update({
                    'rank': rank, 'score': round(student_score, 1), 'participants': participants,
                    'top_score_10': top_score_10, 'top_score_20': top_score_20,
                    'max_score': max_score, 'avg_score': avg_score,
                    'url_answer_input': self.get_url_answer_input(fld) if fld != self.final_field else '',
                })
        return stat_data

    def get_next_url(self, student) -> str:
        for idx, fld in enumerate(self.answer_fields):
            if not student.data[idx][1]:
                return self.get_url_answer_input(fld)
        return self.url_detail

    @staticmethod
    def update_student_score(student, info_answer_student):
        needs_update = False
        for idx, dt in enumerate(student.data):
            score_real = info_answer_student[idx]['score_real']
            if score_real and dt[2] != score_real:
                dt[2] = score_real
                needs_update = True
        if needs_update:
            student.save()

    def update_exam_participants(self, exam, qs_student):
        department_dict = self.department_dict
        participants: dict[str, dict[str | int, dict[str, int]]] = {
            'all': {'total': {fld: 0 for fld in self.admin_score_fields}},
            'filtered': {'total': {fld: 0 for fld in self.admin_score_fields}},
        }
        participants['all'].update({
            d_id: {fld: 0 for fld in self.admin_score_fields} for d_id in department_dict.values()
        })
        participants['filtered'].update({
            d_id: {fld: 0 for fld in self.admin_score_fields} for d_id in department_dict.values()
        })

        for student in qs_student:
            d_id = department_dict[student.department]
            all_confirmed_at = student.answer_all_confirmed_at
            is_filtered = False
            if all_confirmed_at:
                is_filtered = all_confirmed_at < exam.answer_official_opened_at

            for dt in student.data:
                fld = dt[0]
                is_confirmed = dt[1]
                if is_confirmed:
                    participants['all']['total'][fld] += 1
                    participants['all'][d_id][fld] += 1
                if is_filtered:
                    participants['filtered']['total'][fld] += 1
                    participants['filtered'][d_id][fld] += 1
        exam.participants = participants
        exam.save()

        return participants

    @staticmethod
    def update_rank(student, **stat):
        rank: dict[str, dict[str, dict[str, int]]] = {
            'all': {
                'total': {s['field']: s['rank'] for s in stat['stat_total_all']},
                'department': {s['field']: s['rank'] for s in stat['stat_department_all']},
            },
            'filtered': {
                'total': {s['field']: s['rank'] for s in stat['stat_total_filtered']},
                'department': {s['field']: s['rank'] for s in stat['stat_department_filtered']},
            },
        }
        student.rank = rank
        student.save()

    def create_student_instance(self, student):
        with transaction.atomic():
            student.user = self.request.user
            student.year = self.psat_year
            student.exam = self.psat_exam
            student.data = [
                [fld, False, 0, [0 for _ in range(self.problem_count[fld])]] for fld in self.answer_fields
            ]
            student.data.append([self.final_field, False, 0, []])
            student.rank = {
                'all': {
                    'total': {fld: 0 for fld in self.score_fields},
                    'department': {fld: 0 for fld in self.score_fields},
                },
                'filtered': {
                    'total': {fld: 0 for fld in self.score_fields},
                    'department': {fld: 0 for fld in self.score_fields},
                },
            }
            student.save()
        return student
