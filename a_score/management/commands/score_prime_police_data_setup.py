import dataclasses
import traceback
from collections import Counter

import django.db.utils
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from a_score.models import prime_police_models


@dataclasses.dataclass
class CommandScorePrimePoliceExamVars:
    exam_year: int
    exam_round: int
    file_name: str

    exam_model = prime_police_models.PrimePoliceExam
    student_model = prime_police_models.PrimePoliceStudent
    answer_count_model = prime_police_models.PrimePoliceAnswerCount

    subject_fields = [
        'hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob',
    ]
    common_subject_fields = ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']
    subject_vars = {
        '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
        '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
        '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
        '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
    }
    police_subject_fields = {
        '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
        '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
        '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    }
    count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    all_count_fields = count_fields + ['count_multiple', 'count_total']
    dict_score_unit = {
        'hyeongsa': 3, 'gyeongchal': 3,
        'sebeob': 2, 'hoegye': 2, 'jeongbo': 2, 'sine': 2,
        'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
    }

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'round': self.exam_round}

    @property
    def answer_official(self) -> dict[str, list]:
        df = pd.read_excel(self.file_name, sheet_name='정답', header=0, index_col=0)
        df.dropna(inplace=True)
        answer_official = {}
        for subject, answers in df.items():
            answer_official.update({self.police_subject_fields[subject]: [int(ans) for ans in answers]})
        return answer_official

    @property
    def qs_student(self):
        return self.student_model.objects.filter(**self.exam_info)


ONLY_PSAT_FIELDS = ['eoneo', 'jaryo', 'sanghwang']

POLICE_SUBJECT_FIELDS = {
    '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
    '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
    '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    '세법개론': 'sebeob', '회계학': 'hoegye',  # 세무회계 필수
    '상법총칙': 'sangbeob', '경제학': 'gyeongje', '통계학': 'tonggye', '재정학': 'jaejeong',  # 세무회계 선택
    '정보보호론': 'jeongbo', '시스템네트워크보안': 'sine',  # 사이버 필수
    '데이터베이스론': 'debe', '통신이론': 'tongsin', '소프트웨어공학': 'sowe',  # 사이버 선택

}


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Exam year')  # 2024
        parser.add_argument('exam_round', type=str, help='Exam round')  # 1
        parser.add_argument(
            'file_name', type=str, help='Excel file containing official answers and student data ')

    def handle(self, *args, **kwargs):
        exam_year = kwargs['exam_year']
        exam_round = kwargs['exam_round']
        file_name = kwargs['file_name']

        exam_vars = CommandScorePrimePoliceExamVars(exam_year, exam_round, file_name)

        self.stdout.write('================')
        self.stdout.write(f'Create or update exam_model with answer official')
        create_or_update_exam_model(exam_vars)

        self.stdout.write('================')
        self.stdout.write(f'Create or update student_model')
        student_data = get_student_data(exam_vars)
        create_or_update_model(exam_vars.student_model, ['answer', 'answer_count'], student_data)

        self.stdout.write('================')
        self.stdout.write(f'Update student_model for score')
        total_answer_lists, score_data = get_total_answer_lists_and_score_data(exam_vars)
        create_or_update_model(exam_vars.student_model, ['score'], score_data)

        self.stdout.write('================')
        self.stdout.write(f'Update student_model for rank')
        rank_data = get_rank_data(exam_vars)
        rank_matching_fields_for = [
            'rank_total', 'participants_total', 'rank_department', 'participants_department']
        create_or_update_model(exam_vars.student_model, rank_matching_fields_for, rank_data)

        self.stdout.write('================')
        self.stdout.write(f'Create or update answer_count_model')
        total_count = get_total_count(exam_vars, total_answer_lists)
        answer_count_data = get_answer_count_data(exam_vars, total_count)
        matching_fields = exam_vars.all_count_fields + ['answer']
        create_or_update_model(exam_vars.answer_count_model, matching_fields, answer_count_data)


def get_empty_model_data() -> dict:
    return {'update_list': [], 'create_list': [], 'update_count': 0, 'create_count': 0}


def create_or_update_exam_model(exam_vars: CommandScorePrimePoliceExamVars):
    exam_model = exam_vars.exam_model
    answer_official = exam_vars.answer_official
    qs_exam, created = exam_model.objects.get_or_create(**exam_vars.exam_info)
    model_name = exam_model._meta.model_name
    if created:
        qs_exam.answer_official = answer_official
        qs_exam.save()
        message = f'Successfully created {model_name} instance'
    else:
        if qs_exam.answer_official != answer_official:
            qs_exam.answer_official = answer_official
            qs_exam.save()
            message = f'Successfully updated {model_name} instance'
        else:
            message = f'No changes were made to {model_name} instances.'
    print(message)


def get_student_data(exam_vars: CommandScorePrimePoliceExamVars) -> dict:
    student_data = get_empty_model_data()
    student_model = exam_vars.student_model
    df = pd.read_excel(exam_vars.file_name, sheet_name='문항별 표기', header=[0, 1])
    pd.set_option('future.no_silent_downcasting', True)

    for _, student in df.iterrows():
        name = student.loc[('name', 0)]
        serial = student.loc[('serial', 0)]
        selection = student.loc[('selection', 0)]
        password = student.loc[('password', 0)]

        answer_count = {selection: 40}
        selection_cs = student.xs(selection, level=0)
        answer = {selection: selection_cs.fillna(0).infer_objects(copy=False).astype(int).tolist()}
        for field in exam_vars.common_subject_fields:
            cs = student.xs(field, level=0)
            answer[field] = cs.fillna(0).infer_objects(copy=False).astype(int).tolist()
            answer_count[field] = 40

        student_info = {
            'round': exam_vars.exam_round,
            'name': name,
            'serial': serial,
            'selection': selection,
            'password': password,
            'answer': answer,
            'answer_count': answer_count,
        }

        try:
            target_student = student_model.objects.get(
                round=exam_vars.exam_round, name=name, serial=serial, selection=selection, password=password)
            fields_not_match = any([
                target_student.answer != answer,
                target_student.answer_count != answer_count,
            ])
            if fields_not_match:
                target_student.answer = answer
                target_student.answer_count = answer_count
                student_data['update_list'].append(target_student)
                student_data['update_count'] += 1
        except student_model.DoesNotExist:
            student_data['create_list'].append(student_model(**student_info))
            student_data['create_count'] += 1
    return student_data


def get_total_answer_lists_and_score_data(exam_vars: CommandScorePrimePoliceExamVars) -> tuple:
    qs_student = exam_vars.qs_student
    answer_official = exam_vars.answer_official
    score_data = get_empty_model_data()
    total_answer_lists = {field: [] for field in exam_vars.subject_fields}

    for student in qs_student:
        score = {}
        for field, answer in student.answer.items():
            total_answer_lists[field].append(answer)

            correct_count = 0
            score_unit = exam_vars.dict_score_unit.get(field, 1.5)
            for index, ans in enumerate(answer):
                if ans == answer_official[field][index]:
                    correct_count += 1
            score[field] = correct_count * score_unit

        score['sum'] = sum(s for s in score.values())

        if student.score != score:
            student.score = score
            score_data['update_list'].append(student)
            score_data['update_count'] += 1

    return total_answer_lists, score_data


def get_statistics_data(qs_student, stat_type: str, student=None) -> dict:
    score = {}
    participants = {}
    rank = {}

    queryset = qs_student.values('score')
    if stat_type == 'department':
        queryset = qs_student.filter(department=student.department).values('score')

    for field, value in student.score.items():
        score[field] = []
        for qs in queryset:
            if field in qs['score']:
                score[field].append(qs['score'][field])

        participants[field] = len(score[field])
        if field in student.score:
            sorted_score = sorted(score[field], reverse=True)
            rank[field] = sorted_score.index(student.score[field]) + 1

    return {
        f'rank_{stat_type}': rank,
        f'participants_{stat_type}': participants,
    }


def get_rank_data(exam_vars: CommandScorePrimePoliceExamVars) -> dict:
    rank_data = get_empty_model_data()
    qs_student = exam_vars.qs_student
    for student in qs_student:
        stat_dict = get_statistics_data(qs_student=qs_student, stat_type='total', student=student)
        qs_all_score_department = qs_student.filter(department=student.department)
        stat_dict.update(
            get_statistics_data(qs_student=qs_all_score_department, stat_type='department', student=student)
        )
        fields_not_match = any(getattr(student, fld) != val for fld, val in stat_dict.items())
        if fields_not_match:
            for fld, val in stat_dict.items():
                setattr(student, fld, val)
            rank_data['update_list'].append(student)
            rank_data['update_count'] += 1
    return rank_data


def get_total_count(exam_vars: CommandScorePrimePoliceExamVars, total_answer_lists: dict) -> dict:
    total_count: dict[str, list[dict[str, str | int]]] = {}
    for field in exam_vars.subject_fields:
        try:
            answer_official = exam_vars.answer_official[field]
        except KeyError:
            answer_official = None
        total_count[field] = []
        for i in range(1, 41):
            answer = answer_official[i - 1] if answer_official else 0
            append_dict = {
                'year': exam_vars.exam_year, 'exam': '프모', 'round': exam_vars.exam_round,
                'subject': field, 'number': i, 'answer': answer,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0,
                'count_0': 0, 'count_multiple': 0, 'count_total': 0,
            }
            total_count[field].append(append_dict)
    for field, answer_lists in total_answer_lists.items():
        if answer_lists:
            distributions = [Counter() for _ in range(40)]
            for lst in answer_lists:
                for i, value in enumerate(lst):
                    if value > 5:
                        distributions[i]['count_multiple'] += 1
                    else:
                        distributions[i][value] += 1

            for index, counter in enumerate(distributions):
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(5)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                total_count[field][index].update(count_dict)
    return total_count


def get_answer_count_data(exam_vars: CommandScorePrimePoliceExamVars, total_count: dict):
    matching_fields = exam_vars.all_count_fields + ['answer']
    answer_count_data = get_empty_model_data()
    model = exam_vars.answer_count_model
    for field in exam_vars.subject_fields:
        for c in total_count[field]:
            if c['count_total']:
                try:
                    obj = model.objects.get(**exam_vars.exam_info, subject=c['subject'], number=c['number'])
                    fields_not_match = any(getattr(obj, fld) != c[fld] for fld in matching_fields)
                    if fields_not_match:
                        for fld in matching_fields:
                            setattr(obj, fld, c[fld])
                        answer_count_data['update_list'].append(obj)
                        answer_count_data['update_count'] += 1
                except model.DoesNotExist:
                    answer_count_data['create_list'].append(model(**c))
                    answer_count_data['create_count'] += 1
    return answer_count_data


def create_or_update_model(
        model,
        update_fields: list,
        model_data: dict,
):
    model_name = model._meta.model_name
    update_list = model_data['update_list']
    create_list = model_data['create_list']
    update_count = model_data['update_count']
    create_count = model_data['create_count']

    try:
        with transaction.atomic():
            if update_list:
                model.objects.bulk_update(update_list, update_fields)
                message = f'Successfully updated {update_count} {model_name} instances.'
            elif create_list:
                model.objects.bulk_create(create_list)
                message = f'Successfully created {create_count} {model_name} instances.'
            elif not update_list and not create_list:
                message = f'No changes were made to {model_name} instances.'
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = 'An error occurred during the transaction.'
    print(message)
