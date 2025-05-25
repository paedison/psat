import io
import traceback
from urllib.parse import quote

import django.db.utils
from django.db import transaction
from django.http import HttpResponse


def get_sub_list(psat) -> list:
    if psat.exam in ['칠급', '칠예', '민경']:
        return ['언어', '자료', '상황']
    return ['헌법', '언어', '자료', '상황']


def get_subject_vars(psat) -> dict[str, tuple[str, str, int]]:
    subject_vars = {
        '헌법': ('헌법', 'subject_0', 0),
        '언어': ('언어논리', 'subject_1', 1),
        '자료': ('자료해석', 'subject_2', 2),
        '상황': ('상황판단', 'subject_3', 3),
        '평균': ('PSAT 평균', 'average', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        subject_vars.pop('헌법')
    return subject_vars


def get_field_vars(psat, is_filtered=False) -> dict[str, tuple[str, str, int]]:
    if is_filtered:
        field_vars = {
            'filtered_subject_0': ('[필터링]헌법', '[필터링]헌법', 0),
            'filtered_subject_1': ('[필터링]언어', '[필터링]언어논리', 1),
            'filtered_subject_2': ('[필터링]자료', '[필터링]자료해석', 2),
            'filtered_subject_3': ('[필터링]상황', '[필터링]상황판단', 3),
            'filtered_average': ('[필터링]평균', '[필터링]PSAT 평균', 4),
        }
        if psat.exam in ['칠급', '칠예', '민경']:
            field_vars.pop('filtered_subject_0')
        return field_vars
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        field_vars.pop('subject_0')
    return field_vars


def get_total_field_vars(psat) -> dict[str, tuple[str, str, int]]:
    field_vars = {
        'subject_0': ('헌법', '헌법', 0),
        'subject_1': ('언어', '언어논리', 1),
        'subject_2': ('자료', '자료해석', 2),
        'subject_3': ('상황', '상황판단', 3),
        'average': ('평균', 'PSAT 평균', 4),
        'filtered_subject_0': ('[필터링]헌법', '[필터링]헌법', 0),
        'filtered_subject_1': ('[필터링]언어', '[필터링]언어논리', 1),
        'filtered_subject_2': ('[필터링]자료', '[필터링]자료해석', 2),
        'filtered_subject_3': ('[필터링]상황', '[필터링]상황판단', 3),
        'filtered_average': ('[필터링]평균', '[필터링]PSAT 평균', 4),
    }
    if psat.exam in ['칠급', '칠예', '민경']:
        field_vars.pop('subject_0')
        field_vars.pop('filtered_subject_0')
    return field_vars


def get_sub_title_by_psat(year, exam, subject, end_string='기출문제') -> str:
    title_parts = []
    if year:
        title_parts.append(f'{year}년')
        if isinstance(year, str):
            year = int(year)

    if exam:
        exam_dict = {
            '행시': '5급공채/행정고시', '외시': '외교원/외무고시', '칠급': '7급공채',
            '입시': '입법고시', '칠예': '7급공채 예시', '민경': '민간경력', '견습': '견습',
        }
        if not year:
            exam_name = exam_dict[exam]
        else:
            if exam == '행시':
                exam_name = '행정고시' if year < 2011 else '5급공채'
            elif exam == '외시':
                exam_name = '외교원' if year == 2013 else '외무고시'
            elif exam == '칠급':
                exam_name = '7급공채 모의고사' if year == 2020 else '7급공채'
            else:
                exam_name = exam_dict[exam]
        title_parts.append(exam_name)

    if subject:
        subject_dict = {'헌법': '헌법', '언어': '언어논리', '자료': '자료해석', '상황': '상황판단'}
        title_parts.append(subject_dict[subject])

    if not year and not exam and not subject:
        title_parts.append('전체')
    else:
        title_parts.append('전체')
    sub_title = f'{" ".join(title_parts)} {end_string}'
    return sub_title


class BaseConstantList(list):
    def __init__(self, items, label_avg):
        super().__init__(items)
        self.avg_first = [label_avg] + self
        self.avg_last = self + [label_avg]


HAENGSI = {
    'sub': ['헌법', '언어', '자료', '상황'],
    'subject': ['헌법', '언어논리', '자료해석', '상황판단'],
    'sub_field': ['subject_0', 'subject_1', 'subject_2', 'subject_3'],
}

CHILGEUP = {
    'sub': ['언어', '상황', '자료'],
    'subject': ['언어논리', '상황판단', '자료해석'],
    'sub_field': ['subject_1', 'subject_3', 'subject_2'],
}


class ConstantList:
    def __init__(self, exam):
        self.exam = exam

        self.subject_count = 3 if self.exam in ['민경', '칠급'] else 4
        self.sub = self.get_variable_list('sub', 'PSAT 평균')
        self.subject = self.get_variable_list('subject', 'PSAT 평균')
        self.sub_field = self.get_variable_list('sub_field', 'average')
        self.stat_list = ['max', 't10', 't25', 't50', 'avg']
        self.rank_model = BaseConstantList(['rank_total', 'rank_category'], 'rank')
        self.rank_type = BaseConstantList(['top', 'mid', 'low'], 'all')
        self.ac_field = BaseConstantList(
            ['count_1', 'count_2', 'count_3', 'count_4', 'count_5'], 'count_sum')
        self.answer_tab = [{'id': str(idx), 'title': subject} for idx, subject in enumerate(self.subject)]
        self.subject_vars = self.get_subject_vars()

    def get_variable_list(self, key: str, label_avg: str):
        variable_dict = CHILGEUP if self.exam in ['민경', '칠급'] else HAENGSI
        return BaseConstantList(variable_dict[key], label_avg)

    def get_answer_tab(self):
        return [{'id': str(idx), 'title': subject} for idx, subject in enumerate(self.subject)]

    def get_subject_vars(self):
        return {self.sub[idx]: (self.subject[idx], self.sub_field[idx], idx) for idx in range(len(self.sub))}

    @staticmethod
    def get_problem_count_dict(exam):
        if exam == '하프':
            return {'언어': 15, '추리': 20}
        return {'언어': 30, '추리': 40}


def append_list_create(model, list_create, **kwargs):
    try:
        model.objects.get(**kwargs)
    except model.DoesNotExist:
        list_create.append(model(**kwargs))


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


def get_response_for_excel_file(df, filename):
    excel_data = io.BytesIO()
    df.to_excel(excel_data, engine='xlsxwriter')

    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={quote(filename)}'

    return response
