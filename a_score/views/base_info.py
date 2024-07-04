import os

import pandas as pd
from django.conf import settings
from django.db import transaction
from django.db.models import Count, QuerySet, F
from django.urls import reverse_lazy
from pandas import DataFrame

from common.constants import icon_set_new
from common.utils import detect_encoding, HtmxHttpRequest
from a_score.models import (
    PrimePsatExam, PrimePsatStudent, PrimePsatAnswerCount
)


class ExamInfo:
    # Target Exam
    YEAR = 2024
    EXAM = '행시'
    ROUND = 0

    # Subject full name, field
    HEONBEOB = ('헌법', 'heonbeob')
    EONEO = ('언어논리', 'eoneo')
    JARYO = ('자료해석', 'jaryo')
    SANGHWANG = ('상황판단', 'sanghwang')
    PSAT_TOTAL = ('PSAT 총점', 'psat')
    PSAT_AVG = ('PSAT 평균', 'psat_avg')

    # Subject variables dictionary
    SUBJECT_VARS = {
        '헌법': HEONBEOB,
        '언어': EONEO,
        '자료': JARYO,
        '상황': SANGHWANG,
        '총점': PSAT_TOTAL,
        '평균': PSAT_AVG,
    }
    FIELD_VARS = {
        'heonbeob': ('헌법', '헌법'),
        'eoneo': ('언어', '언어논리'),
        'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'),
        'psat_total': ('총점', 'PSAT 총점'),
        'psat_avg': ('평균', 'PSAT 평균'),
    }

    # Customize PROBLEM_COUNT, SUBJECT_VARS by Exam
    if EXAM == '칠급':
        PROBLEM_COUNT = {'eoneo': 25, 'jaryo': 25, 'sanghwang': 25}
        SUBJECT_VARS.pop('헌법')
    else:
        PROBLEM_COUNT = {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}

    # View info
    INFO = {
        'menu': 'predict',
        'view_type': 'predict',
    }

    # Queryset variables
    qs_exam = PrimePsatExam.objects.filter(exam=EXAM, round=ROUND)
    qs_student = PrimePsatStudent.objects.filter(year=YEAR, exam=EXAM, round=ROUND)
    qs_answer_count = PrimePsatAnswerCount.objects.filter(
        year=YEAR, exam=EXAM, round=ROUND).annotate(no=F('number')).order_by('subject', 'number')

    def get_obj_student(self, request: HtmxHttpRequest) -> PrimePsatStudent:
        return self.qs_student.filter(user=request.user).first()

    def get_dict_data_answer_rate(self, data_answer_official: dict, qs_answer_count) -> dict:
        dict_answer_count = {field: [] for field in self.PROBLEM_COUNT.keys()}

        qs: PrimePsatAnswerCount
        for qs in qs_answer_count:
            field = self.SUBJECT_VARS[qs.subject][1]
            dict_answer_count[field].append(qs)
            if data_answer_official:
                answer_official = data_answer_official[field][qs.number - 1]
                ans_official = answer_official['ans']
                qs.rate_correct = getattr(qs, f'rate_{ans_official}')
                answer_official['rate_correct'] = getattr(qs, f'rate_{ans_official}')

        return dict_answer_count

    @staticmethod
    def get_list_answer_empty(problem_count: int) -> list:
        answer_empty = []
        for i in range(1, problem_count + 1):
            answer_empty.append({'no': i, 'ans': ''})
        return answer_empty

    def get_dict_info_answer_student_empty(self, field):
        sub = self.FIELD_VARS[field][0]
        return {
            'icon': icon_set_new.ICON_SUBJECT[sub],
            'sub': sub,
            'subject': self.SUBJECT_VARS[sub][0],
            'field': self.SUBJECT_VARS[sub][1],
        }
