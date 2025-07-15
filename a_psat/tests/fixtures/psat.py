__all__ = [
    'psat_test_psat', 'psat_urls', 'psat_test_predict_psat',
    'psat_test_problems', 'psat_test_answer_counts'
]

from collections import defaultdict

import pytest
from django.urls import reverse

from a_psat.tests import factories
from .common import psat_test_exam_info, psat_time_schedule, psat_subject_vars


@pytest.fixture
def psat_test_psat(psat_test_exam_info):
    return factories.PsatFactory(**psat_test_exam_info)


@pytest.fixture
def psat_urls(psat_test_psat, psat_subject_vars):
    psat_urls = {
        'detail': reverse('psat:predict-detail', args=[psat_test_psat.id]),
        'register': reverse('psat:predict-register'),
    }
    for (_, subject_fld, field_idx, _) in psat_subject_vars.values():
        psat_urls[f'answer_input_{field_idx}'] = reverse(
            'psat:predict-answer-input', args=[psat_test_psat.id, subject_fld])
        psat_urls[f'answer_confirm_{field_idx}'] = reverse(
            'psat:predict-answer-confirm', args=[psat_test_psat.id, subject_fld])
    return psat_urls


@pytest.fixture
def psat_test_predict_psat(psat_test_psat, psat_time_schedule):
    def get_time(key):
        return {key: psat_time_schedule[key]}

    return factories.PredictPsatFactory(
        psat=psat_test_psat,
        is_active=True,
        **get_time('exam_started_at'),
        **get_time('exam_finished_at'),
        **get_time('answer_predict_opened_at'),
        **get_time('answer_official_opened_at'),
        **get_time('predict_closed_at'),
    )


@pytest.fixture
def psat_test_problems(psat_test_psat, psat_subject_vars):
    created = []
    for sub, (_, _, _, count) in psat_subject_vars.items():
        for number in range(1, count + 1):
            created.append(factories.ProblemFactory(psat=psat_test_psat, subject=sub, number=number))
    return created


@pytest.fixture
def psat_test_answer_counts(psat_test_problems, psat_subject_vars):
    created = defaultdict(list)
    factories_dict = {
        'all': factories.PredictAnswerCountFactory,
        'top': factories.PredictAnswerCountTopRankFactory,
        'mid': factories.PredictAnswerCountMidRankFactory,
        'low': factories.PredictAnswerCountLowRankFactory,
    }
    for problem in psat_test_problems:
        for key, factory in factories_dict.items():
            created[key].append(factory(problem=problem))
    return created
