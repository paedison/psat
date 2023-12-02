import numpy as np
from django.db.models import (
    F, Count, Max, Avg
)
from django.db.models import Window
from django.db.models.functions import Rank, PercentRank


def get_rank_qs(queryset):
    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    def rank_ratio_func(field_name) -> Window:
        return Window(expression=PercentRank(), order_by=F(field_name).desc())

    return queryset.annotate(
        eoneo_rank=rank_func('eoneo_score'),
        eoneo_rank_ratio=rank_ratio_func('eoneo_score'),
        jaryo_rank=rank_func('jaryo_score'),
        jaryo_rank_ratio=rank_ratio_func('jaryo_score'),
        sanghwang_rank=rank_func('sanghwang_score'),
        sanghwang_rank_ratio=rank_ratio_func('sanghwang_score'),
        psat_rank=rank_func('psat_score'),
        psat_rank_ratio=rank_ratio_func('psat_score'),
        heonbeob_rank=rank_func('heonbeob_score'),
        heonbeob_rank_ratio=rank_ratio_func('heonbeob_score'),
    )


def get_stat(queryset) -> dict:
    stat_queryset = queryset.aggregate(
        num_students=Count('id'),

        eoneo_score_max=Max('eoneo_score', default=0),
        jaryo_score_max=Max('jaryo_score', default=0),
        sanghwang_score_max=Max('sanghwang_score', default=0),
        psat_average_max=Max('psat_score', default=0) / 3,
        heonbeob_score_max=Max('heonbeob_score', default=0),

        eoneo_score_avg=Avg('eoneo_score', default=0),
        jaryo_score_avg=Avg('jaryo_score', default=0),
        sanghwang_score_avg=Avg('sanghwang_score', default=0),
        psat_average_avg=Avg('psat_score', default=0) / 3,
        heonbeob_score_avg=Avg('heonbeob_score', default=0),
    )

    score_list_all = list(queryset.values(
        'eoneo_score', 'jaryo_score', 'sanghwang_score', 'psat_score', 'heonbeob_score'))
    score_list_eoneo = [s['eoneo_score'] for s in score_list_all]
    score_list_jaryo = [s['jaryo_score'] for s in score_list_all]
    score_list_sanghwang = [s['sanghwang_score'] for s in score_list_all]
    score_list_psat = [s['psat_score'] for s in score_list_all]
    score_list_heonbeob = [s['heonbeob_score'] for s in score_list_all]

    def get_top_score(score_list: str):
        return np.percentile(score_list, [90, 80], interpolation='nearest')

    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat = get_top_score(score_list_psat)
    top_score_heonbeob = get_top_score(score_list_heonbeob)

    try:
        stat_queryset['eoneo_score_10'] = top_score_eoneo[0]
        stat_queryset['eoneo_score_20'] = top_score_eoneo[1]
        stat_queryset['jaryo_score_10'] = top_score_jaryo[0]
        stat_queryset['jaryo_score_20'] = top_score_jaryo[1]
        stat_queryset['sanghwang_score_10'] = top_score_sanghwang[0]
        stat_queryset['sanghwang_score_20'] = top_score_sanghwang[1]
        stat_queryset['psat_average_10'] = top_score_psat[0] / 3
        stat_queryset['psat_average_20'] = top_score_psat[1] / 3
        stat_queryset['heonbeob_score_10'] = top_score_heonbeob[0]
        stat_queryset['heonbeob_score_20'] = top_score_heonbeob[1]
    except TypeError:
        pass

    return stat_queryset
