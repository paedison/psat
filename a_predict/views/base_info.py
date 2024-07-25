import dataclasses
from typing import Type

from django.db import transaction
from django.db.models import QuerySet, F
from django.urls import reverse

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest
from .. import forms, models


@dataclasses.dataclass
class PredictExamVars:
    request: HtmxHttpRequest
    exam_type: str
    exam_year: int
    exam_exam: str
    exam_round: int
    selection: str = ''
    is_admin: bool = False

    # Template variables
    data_answer_predict: list[list[dict]] = dataclasses.field(default_factory=list)
    answer_confirmed: list[bool] = dataclasses.field(default_factory=list)
    data_answer_official_tuple: tuple[list[list[dict]], bool] = dataclasses.field(default_factory=tuple)
    data_answer_student: list[list[dict]] = dataclasses.field(default_factory=list)
    info_answer_student: list = dataclasses.field(default_factory=list)
    stat: dict[str, list[dict]] = dataclasses.field(default_factory=dict)

    # common vars
    default_count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    extra_count_fields = ['count_multiple', 'count_total']
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']
    subject_to_field_dict = {
        '언어논리': 'eoneo', '자료해석': 'jaryo', '상황판단': 'sanghwang',
        '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
        '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
        '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    }
    field_to_subject_dict = {
        'eoneo': '언어논리', 'jaryo': '자료해석', 'sanghwang': '상황판단',
        'hyeongsa': '형사법', 'heonbeob': '헌법',  # 전체 공통
        'gyeongchal': '경찰학', 'beomjoe': '범죄학',  # 일반 필수
        'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙',  # 일반 선택
    }
    subject_vars = {
        '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
        '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
        '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
        '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
        '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
    }
    field_vars = {
        'eoneo': ('언어', '언어논리'), 'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'), 'psat_avg': ('평균', 'PSAT 평균'),
        'hyeongsa': ('형사', '형사학'), 'heonbeob': ('헌법', '헌법'),
        'gyeongchal': ('경찰', '경찰학'), 'beomjoe': ('범죄', '범죄학'),
        'haengbeob': ('행법', '행정법'), 'haenghag': ('행학', '행정학'), 'minbeob': ('민법', '민법총칙'),
    }

    info = {'menu': 'predict', 'view_type': 'predict'}
    icon_menu = icon_set_new.ICON_MENU['predict']
    score_template_table_1 = 'a_predict/snippets/index_sheet_score_table_1.html'
    score_template_table_2 = 'a_predict/snippets/index_sheet_score_table_2.html'
    score_tab = {
        'id': '012',
        'title': ['내 성적', '전체 기준', '직렬 기준'],
        'template': [score_template_table_1, score_template_table_2, score_template_table_2],
    }

    # psat/police vars
    only_psat_fields = ['eoneo', 'jaryo', 'sanghwang']
    police_common_fields = ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']

    @property
    def is_psat(self) -> bool:
        return self.exam_type == 'psat'

    @property
    def exam_model(self) -> Type[models.PsatExam | models.PoliceExam]:
        if self.is_psat:
            return models.PsatExam
        return models.PoliceExam

    @property
    def unit_model(self) -> Type[models.PsatUnit | models.PoliceUnit]:
        if self.is_psat:
            return models.PsatUnit
        return models.PoliceUnit

    @property
    def department_model(self) -> Type[models.PsatDepartment | models.PoliceDepartment]:
        if self.is_psat:
            return models.PsatDepartment
        return models.PoliceDepartment

    @property
    def student_model(self) -> Type[models.PsatStudent | models.PoliceStudent]:
        if self.is_psat:
            return models.PsatStudent
        return models.PoliceStudent

    @property
    def location_model(self) -> Type[models.PsatLocation | None]:
        if self.is_psat:
            return models.PsatLocation

    @property
    def answer_count_model(self) -> Type[models.PsatAnswerCount | models.PoliceAnswerCount]:
        if self.is_psat:
            return models.PsatAnswerCount
        return models.PoliceAnswerCount

    @property
    def student_form(self) -> Type[forms.PsatStudentForm | forms.PoliceStudentForm]:
        if self.is_psat:
            return forms.PsatStudentForm
        return forms.PoliceStudentForm

    @property
    def exam_info(self) -> dict:
        return {'year': self.exam_year, 'exam': self.exam_exam, 'round': self.exam_round}

    @property
    def student_exam_info(self) -> dict:
        return {
            'student__year': self.exam_year, 'student__exam': self.exam_exam, 'student__round': self.exam_round
        }

    @property
    def exam_url_kwargs(self) -> dict:
        return {
            'exam_type': self.exam_type, 'exam_year': self.exam_year,
            'exam_exam': self.exam_exam, 'exam_round': self.exam_round
        }

    @property
    def exam(self) -> Type[models.PsatExam | models.PoliceExam]:
        return self.exam_model.objects.filter(**self.exam_info).first()

    @property
    def all_units(self) -> list:
        return self.unit_model.objects.filter(exam=self.exam_exam).values_list('name', flat=True)

    @property
    def qs_department(self) -> QuerySet:
        return self.department_model.objects.filter(exam=self.exam_exam).order_by('order')

    @property
    def department_dict(self) -> dict[str, int]:
        qs_department = self.department_model.objects.filter(exam=self.exam_exam).order_by('order')
        return {department.name: department.id for department in qs_department}

    @property
    def qs_student(self) -> QuerySet:
        return self.student_model.objects.filter(**self.exam_info)

    @property
    def student(self) -> Type[models.PsatStudent | models.PoliceStudent]:
        if self.request.user.is_authenticated:
            return self.student_model.objects.filter(**self.exam_info, user=self.request.user).first()

    @property
    def qs_answer_count(self) -> QuerySet:
        return self.answer_count_model.objects.filter(**self.exam_info).annotate(
            no=F('number')).order_by('subject', 'number')

    @property
    def sub_list(self) -> list[str]:
        if self.is_psat:
            if self.exam_exam == '칠급':
                return ['언어', '상황', '자료']
            return ['헌법', '언어', '자료', '상황']
        police_common_sub_list = ['형사', '헌법', '경찰', '범죄']
        default = {'haengbeob': '행법', 'haenghag': '행학', 'minbeob': '민법'}
        return police_common_sub_list + [default[self.selection]]

    @property
    def subject_list(self) -> list[str]:
        chilgeup = ['언어논리', '상황판단', '자료해석']
        haengsi = ['헌법', '언어논리', '자료해석', '상황판단']
        if self.is_psat:
            if self.is_admin:
                return ['PSAT'] + self.subject_list
            else:
                if self.exam_exam == '칠급':
                    return chilgeup
                return haengsi
        police_common = ['형사학', '헌법', '경찰학', '범죄학']
        if self.is_admin:
            return ['총점'] + police_common + ['민법총칙', '행정학', '행정법']
        else:
            default = {'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙'}
            return police_common + [default[self.selection]]

    @property
    def answer_fields(self) -> list[str]:
        if self.is_psat:
            if self.exam_exam == '칠급':
                return ['eoneo', 'sanghwang', 'jaryo']
            return ['heonbeob'] + self.only_psat_fields
        return self.police_common_fields + [self.selection]

    @property
    def all_subject_fields(self) -> list[str]:
        if self.is_psat:
            return self.answer_fields
        return self.police_common_fields + ['minbeob', 'haenghag', 'haengbeob']

    @property
    def all_police_subject_fields(self) -> list[str]:
        return self.police_common_fields + ['minbeob', 'haenghag', 'haengbeob']

    @property
    def selection_choice(self) -> list[dict[str, str]]:
        return [
            {'field': 'minbeob', 'name': '민법총칙'},
            {'field': 'haenghag', 'name': '행정학'},
            {'field': 'haengbeob', 'name': '행정법'},
        ]

    @property
    def final_field(self) -> str:
        return 'psat_avg' if self.is_psat else 'sum'

    @property
    def score_fields(self) -> list:
        if self.is_admin:
            return [self.final_field] + self.answer_fields
        return self.answer_fields + [self.final_field]

    @property
    def problem_count(self) -> dict[str, int]:
        if self.is_psat:
            if self.exam_exam == '칠급':
                return {'eoneo': 25, 'jaryo': 25, 'sanghwang': 25}
            return {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}
        return {fld: 40 for fld in self.answer_fields}

    @property
    def count_fields(self) -> list[str]:
        default_count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
        if self.is_psat:
            return default_count_fields + ['count_5']
        return default_count_fields

    @property
    def all_count_fields(self) -> list[str]:
        return self.count_fields + ['count_multiple', 'count_total']

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
    def url_answer_input(self) -> list:
        kwargs_dict = [dict(self.exam_url_kwargs, **{'subject_field': fld}) for fld in self.answer_fields]
        return [reverse('predict:answer-input', kwargs=kwargs) for kwargs in kwargs_dict]

    def get_url_answer_input(self, subject_field) -> list:
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
    def sub_title(self) -> str:
        default = {
            'psat': {
                '프모': f'제{self.exam_round}회 프라임모의고사 합격 예측',
                '행시': f'{self.exam_year}년 5급공채 등 합격 예측',
                '칠급': f'{self.exam_year}년 7급공채 등 합격 예측',
            },
            'police': {
                '프모': f'제{self.exam_round}회 프라임모의고사 합격 예측',
                '경위': f'74기 경위공채 합격 예측',
            }
        }
        return default[self.exam_type][self.exam_exam]

    @property
    def icon_subject(self) -> list[str]:
        if self.is_psat:
            return [icon_set_new.ICON_SUBJECT[sub] for sub in self.sub_list]
        return ['' for _ in self.sub_list]

    @property
    def info_tab(self) -> dict[str, str]:
        return {'id': ''.join([str(i) for i in range(len(self.score_fields))])}

    @property
    def answer_tab(self) -> dict[str, str]:
        return {
            'id': ''.join([str(i) for i in range(len(self.sub_list))]),
            'title': self.sub_list,
            'url_answer_input': self.url_answer_input,
        }

    def get_location(self, student) -> models.PsatLocation:
        if self.location_model:
            serial = int(student.serial)
            return self.location_model.objects.filter(
                **self.exam_info, serial_start__lte=serial, serial_end__gte=serial).first()

    def get_exam(self) -> models.PsatExam | models.PoliceExam:
        return self.exam_model.objects.filter(**self.exam_info).first()

    def get_qs_department(self, unit=None) -> models.PsatDepartment | models.PoliceDepartment:
        if unit:
            return self.department_model.objects.filter(exam=self.exam_exam, unit=unit).order_by('order')
        return self.department_model.objects.filter(exam=self.exam_exam).order_by('order')

    def get_student(self) -> models.PsatStudent | models.PoliceStudent:
        return self.student_model.objects.filter(**self.exam_info, user=self.request.user).first()

    def get_problem_info(self, field: str, number: int) -> dict:
        return dict(self.exam_info, **{'subject': field, 'number': number})

    def get_subject_field(self, subject) -> str:
        for fld, sub_tuple in self.field_vars.items():
            if fld == subject or sub_tuple[0] == subject or sub_tuple[1] == subject:
                return fld

    def get_problem_count(self, field) -> int:
        if self.is_psat:
            if self.exam_exam == '칠급' or field in ['heonbeob', '헌법']:
                return 25
        return 40

    def get_score_unit(self, field) -> float | int:
        if self.is_psat:
            if self.exam_exam == '칠급' or field in ['heonbeob', '헌법']:
                return 4
            return 2.5
        police_score_unit = {
            'hyeongsa': 3, 'gyeongchal': 3, 'sebeob': 2, 'hoegye': 2, 'jeongbo': 2,
            'sine': 2, 'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
        }
        return police_score_unit.get(field, 1.5)

    def get_empty_data_answer(self) -> list[list[dict[str, int | str]]]:
        return [
            [
                {'no': no, 'ans': 0, 'field': fld}
                for no in range(1, self.get_problem_count(fld) + 1)
            ] for fld in self.answer_fields
        ]

    def get_field_idx(self, field) -> int:
        return self.score_fields.index(field)

    def get_field_name(self, subject) -> str:
        return self.subject_to_field_dict[subject]

    def get_subject_name(self, field) -> str:
        return self.field_to_subject_dict[field]

    def get_data_answer_official(self, exam) -> tuple[list, bool]:
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
        data_answer_official = self.get_empty_data_answer()
        if exam and exam.is_answer_official_opened:
            official_answer_uploaded = True
            try:
                for field, answer in exam.answer_official.items():
                    field_idx = self.get_field_idx(field)
                    for no, ans in enumerate(answer, start=1):
                        data_answer_official[field_idx][no - 1] = {'no': no, 'ans': ans, 'field': field}
            except IndexError:
                official_answer_uploaded = False
            except KeyError:
                official_answer_uploaded = False
        self.data_answer_official_tuple = data_answer_official, official_answer_uploaded
        return data_answer_official, official_answer_uploaded

    def get_data_answer_predict(self) -> list:
        data_answer_predict = self.get_empty_data_answer()
        for answer_count in self.qs_answer_count:
            field = answer_count.subject
            if field in self.answer_fields:
                field_idx = self.answer_fields.index(field)
                no = answer_count.number

                count_list = [getattr(answer_count, c) for c in self.count_fields]
                ans_predict = count_list[1:].index(max(count_list[1:])) + 1
                rate_accuracy = round(getattr(answer_count, f'rate_{ans_predict}'), 1)

                count_list.extend([answer_count.count_multiple, answer_count.count_total])

                data_answer_predict[field_idx][no - 1].update({
                    'no': no, 'ans': ans_predict, 'field': field,
                    'rate_accuracy': rate_accuracy, 'count': count_list,
                })

        return data_answer_predict

    def get_data_answer_student(self, student) -> list:
        data_answer_student = self.get_empty_data_answer()
        data_answer_official = self.data_answer_official_tuple[0]
        official_answer_uploaded = data_answer_official[1]

        for field_idx, val in enumerate(self.data_answer_predict):
            is_confirmed = student.data[field_idx][1]
            if is_confirmed:
                for no_idx, answer_predict in enumerate(val):
                    ans_student = student.data[field_idx][-1][no_idx]
                    ans_predict = answer_predict['ans']
                    count_total = answer_predict['count'][-1]
                    rate_selection = 0
                    if count_total:
                        rate_selection = round(answer_predict['count'][ans_student] * 100 / count_total, 1)

                    prediction_is_correct = result = None
                    if official_answer_uploaded:
                        ans_official = data_answer_official[field_idx][no_idx]['ans']
                        prediction_is_correct = ans_official == ans_predict
                        answer_predict['prediction_is_correct'] = ans_official == ans_predict
                        if 1 <= ans_official <= 5:
                            result = ans_student == ans_official
                            rate_correct = round(answer_predict['count'][ans_official] * 100 / count_total, 1)
                        else:
                            ans_official_list = [int(ans) for ans in str(ans_official)]
                            result = ans_student in ans_official_list
                            rate_correct = round(sum(
                                answer_predict['count'][ans] for ans in ans_official_list) * 100 / count_total, 1)
                        data_answer_official[field_idx][no_idx]['rate_correct'] = rate_correct

                    answer_predict['prediction_is_correct'] = prediction_is_correct
                    data_answer_student[field_idx][no_idx].update({
                        'no': no_idx + 1,
                        'ans': ans_student,
                        'rate_selection': rate_selection,
                        'result_real': result,
                    })
        return data_answer_student

    def get_info_answer_student(self, exam, student) -> list:
        info_answer_student: list[dict] = [{} for _ in self.score_fields]

        score_predict_sum = 0
        participants = exam.participants['all']['total']

        answer_count_sum = 0
        for fld in self.score_fields:
            field_idx = self.score_fields.index(fld)
            sub, subject = self.field_vars[fld]
            is_confirmed = student.data[field_idx][1]
            score_real = student.data[field_idx][-2]
            answer_student = student.data[field_idx][-1]
            answer_count = len([x for x in answer_student if x != 0])
            answer_count_sum += answer_count

            if fld != self.final_field:
                correct_predict_count = 0
                for idx, answer_student in enumerate(self.data_answer_student[field_idx]):
                    ans_student = answer_student['ans']
                    ans_predict = self.data_answer_predict[field_idx][idx]['ans']

                    result_predict = ans_student == ans_predict
                    answer_student['result_predict'] = result_predict
                    correct_predict_count += 1 if result_predict else 0

                problem_count = self.problem_count[fld]
                score_predict = correct_predict_count * 100 / problem_count
                if fld in self.only_psat_fields + self.all_police_subject_fields:
                    score_predict_sum += score_predict
            else:
                problem_count = sum([val for val in self.problem_count.values()])
                score_predict = score_predict_sum / 3
                answer_count = answer_count_sum
            url_answer_input = self.url_answer_input[field_idx] if fld in self.answer_fields else ''

            info_answer_student[field_idx].update({
                'icon': icon_set_new.ICON_SUBJECT[sub],
                'sub': sub, 'subject': subject, 'field': fld,
                'is_confirmed': is_confirmed,
                'participants': participants[fld],
                'score_real': score_real, 'score_predict': score_predict,
                'problem_count': problem_count, 'answer_count': answer_count,
                'url_answer_input': url_answer_input,
            })
        return info_answer_student

    def get_stat_data(self, exam, student, stat_type: str, filtered: bool = False) -> list:
        score_list = {fld: [] for fld in self.score_fields}
        stat_data = []
        for fld_idx, fld in enumerate(self.score_fields):
            sub, subject = self.field_vars[fld]
            stat_data.append({
                'field': fld, 'sub': sub, 'subject': subject,
                'icon': icon_set_new.ICON_SUBJECT[sub],
                'is_confirmed': student.data[fld_idx][1],
                'rank': 0, 'score': 0, 'participants': 0,
                'max_score': 0, 'top_score_10': 0,
                'top_score_20': 0, 'avg_score': 0,
            })

        filter_exp = {}
        if stat_type == 'department':
            filter_exp['department'] = student.department
        if filtered:
            filter_exp['answer_all_confirmed_at__lte'] = exam.answer_official_opened_at
        qs_student = self.qs_student.filter(**filter_exp)

        for fld_idx, fld in enumerate(self.score_fields):
            for stu in qs_student:
                if stu.data[fld_idx][1]:
                    score_list[fld].append(stu.data[fld_idx][-2])

            if score_list[fld]:
                participants = len(score_list[fld])
                sorted_scores = sorted(score_list[fld], reverse=True)

                student_score = student.data[fld_idx][-2]
                rank = sorted_scores.index(student_score) + 1
                top_10_threshold = max(1, int(participants * 0.1))
                top_20_threshold = max(1, int(participants * 0.2))

                stat_data[fld_idx].update({
                    'rank': rank, 'score': round(student_score, 1), 'participants': participants,
                    'max_score': round(sorted_scores[0], 1),
                    'top_score_10': round(sorted_scores[top_10_threshold - 1], 1),
                    'top_score_20': round(sorted_scores[top_20_threshold - 1], 1),
                    'avg_score': round(sum(score_list[fld]) / participants if participants else 0, 1),
                })
        return stat_data

    def get_next_url(self, student) -> str:
        for idx, fld in enumerate(self.answer_fields):
            if not student.data[idx][1]:
                url_kwargs = self.exam_url_kwargs.copy()
                url_kwargs['subject_field'] = fld
                return self.url_answer_input[idx]
        return self.url_detail

    def update_exam_participants(self, exam):
        department_dict = self.department_dict
        participants = {
            'all': {'total': {fld: 0 for fld in self.score_fields}},
            'filtered': {'total': {fld: 0 for fld in self.score_fields}},
        }
        participants['all'].update({
            d_id: {fld: 0 for fld in self.score_fields} for d_id in department_dict.values()
        })
        participants['filtered'].update({
            d_id: {fld: 0 for fld in self.score_fields} for d_id in department_dict.values()
        })

        for student in self.qs_student:
            d_id = department_dict[student.department]
            for fld_idx, dt in enumerate(student.data):
                if dt[1]:
                    participants['all']['total'][dt[0]] += 1
                    participants['all'][d_id][dt[0]] += 1

                all_confirmed_at = student.answer_all_confirmed_at
                if all_confirmed_at and all_confirmed_at < exam.answer_official_opened_at:
                    participants['filtered']['total'][dt[0]] += 1
                    participants['filtered'][d_id][dt[0]] += 1
        exam.participants = participants
        exam.save()

        return participants

    @staticmethod
    def update_rank(student, **stat):
        rank = {
            'all': {
                'total': {s['field']: s['rank'] for s in stat['stat_total_all']},
                'department': {s['field']: s['rank'] for s in stat['stat_department_all']},
            },
            'filtered': {
                'total': {s['field']: s['rank'] for s in stat['stat_total_filtered']},
                'department': {s['field']: s['rank'] for s in stat['stat_department_filtered']},
            },
        }
        if student.rank != rank:
            student.rank = rank
            student.save()

    def create_student_instance(self, student):
        with transaction.atomic():
            student.user = self.request.user
            student.year = self.exam_year
            student.exam = self.exam_exam
            student.round = self.exam_round
            student.data = [
                [fld, False, [0 for _ in range(self.problem_count[fld])]] for fld in self.answer_fields
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
