import numpy as np
from django.db.models import F, Count, Max, Avg
from django.db.models import Window
from django.db.models.functions import Rank, PercentRank


def get_dict_by_sub(target_list: list[dict]) -> dict:
    result_dict = {'헌법': [], '언어': [], '자료': [], '상황': []}
    for key in result_dict.keys():
        result_list = []
        for t in target_list:
            if t and t['sub'] == key:
                result_list.append(t)
        result_dict[key] = result_list
    return result_dict


def get_rank_qs(queryset):
    def rank_func(field_name) -> Window:
        return Window(expression=Rank(), order_by=F(field_name).desc())

    def rank_ratio_func(field_name) -> Window:
        return Window(expression=PercentRank(), order_by=F(field_name).desc())

    return queryset.annotate(
        user_id=F('student__user_id'),

        rank_heonbeob=rank_func('score_heonbeob'),
        rank_eoneo=rank_func('score_eoneo'),
        rank_jaryo=rank_func('score_jaryo'),
        rank_sanghwang=rank_func('score_sanghwang'),
        rank_psat=rank_func('score_psat_avg'),

        rank_ratio_heonbeob=rank_ratio_func('score_heonbeob'),
        rank_ratio_eoneo=rank_ratio_func('score_eoneo'),
        rank_ratio_jaryo=rank_ratio_func('score_jaryo'),
        rank_ratio_sanghwang=rank_ratio_func('score_sanghwang'),
        rank_ratio_psat=rank_ratio_func('score_psat_avg'),
    )


def get_all_ranks_dict(get_students_qs, user_id) -> dict:
    rank_total = rank_department = None

    students_qs_total = get_students_qs('전체')
    rank_qs_total = get_rank_qs(students_qs_total).values()
    for qs in rank_qs_total:
        if qs['user_id'] == user_id:
            rank_total = qs

    students_qs_department = get_students_qs('직렬')
    rank_qs_department = get_rank_qs(students_qs_department).values()
    for qs in rank_qs_department:
        if qs['user_id'] == user_id:
            rank_department = qs

    return {
        '전체': rank_total,
        '직렬': rank_department,
    }


def get_top_score(score_list: list):
    try:
        return np.percentile(score_list, [90, 80], interpolation='nearest')
    except IndexError:
        return [0, 0]
    except TypeError:
        return [0, 0]


def get_stat(queryset) -> dict:
    stat_queryset = queryset.aggregate(
        num_students=Count('id'),

        max_score_heonbeob=Max('score_heonbeob', default=0),
        max_score_eoneo=Max('score_eoneo', default=0),
        max_score_jaryo=Max('score_jaryo', default=0),
        max_score_sanghwang=Max('score_sanghwang', default=0),
        max_score_psat_avg=Max('score_psat_avg', default=0) / 3,

        avg_score_heonbeob=Avg('score_heonbeob', default=0),
        avg_score_eoneo=Avg('score_eoneo', default=0),
        avg_score_jaryo=Avg('score_jaryo', default=0),
        avg_score_sanghwang=Avg('score_sanghwang', default=0),
        avg_score_psat_avg=Avg('score_psat_avg', default=0) / 3,
    )

    score_list_all = list(queryset.values(
        'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat_avg', 'score_heonbeob'))
    score_list_heonbeob = [s['score_heonbeob'] for s in score_list_all]
    score_list_eoneo = [s['score_eoneo'] for s in score_list_all]
    score_list_jaryo = [s['score_jaryo'] for s in score_list_all]
    score_list_sanghwang = [s['score_sanghwang'] for s in score_list_all]
    score_psat_avg = [s['score_psat_avg'] for s in score_list_all]

    top_score_heonbeob = get_top_score(score_list_heonbeob)
    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat_avg = get_top_score(score_psat_avg)

    try:
        stat_queryset['top_score_10_heonbeob'] = top_score_heonbeob[0]
        stat_queryset['top_score_20_heonbeob'] = top_score_heonbeob[1]

        stat_queryset['top_score_10_eoneo'] = top_score_eoneo[0]
        stat_queryset['top_score_20_eoneo'] = top_score_eoneo[1]

        stat_queryset['top_score_10_jaryo'] = top_score_jaryo[0]
        stat_queryset['top_score_20_jaryo'] = top_score_jaryo[1]

        stat_queryset['top_score_10_sanghwang'] = top_score_sanghwang[0]
        stat_queryset['top_score_20_sanghwang'] = top_score_sanghwang[1]

        stat_queryset['top_score_10_psat_avg'] = top_score_psat_avg[0]
        stat_queryset['top_score_20_psat_avg'] = top_score_psat_avg[1]
    except TypeError:
        pass

    return stat_queryset


def get_all_stat_dict(get_students_qs, student) -> dict:
    stat_total = stat_department = None

    if student:
        students_qs_total = get_students_qs('전체')
        stat_total = get_stat(students_qs_total)

        students_qs_department = get_students_qs('직렬')
        stat_department = get_stat(students_qs_department)

    return {
        '전체': stat_total,
        '직렬': stat_department,
    }


def get_score_stat(queryset) -> dict:
    stat_queryset = queryset.aggregate(
        num_students=Count('id'),

        max_score_heonbeob=Max('score_heonbeob', default=0),
        max_score_eoneo=Max('score_eoneo', default=0),
        max_score_jaryo=Max('score_jaryo', default=0),
        max_score_sanghwang=Max('score_sanghwang', default=0),
        max_score_psat_avg=Max('score_psat_avg', default=0),

        avg_score_heonbeob=Avg('score_heonbeob', default=0),
        avg_score_eoneo=Avg('score_eoneo', default=0),
        avg_score_jaryo=Avg('score_jaryo', default=0),
        avg_score_sanghwang=Avg('score_sanghwang', default=0),
        avg_score_psat_avg=Avg('score_psat_avg', default=0),
    )

    score_list_all = list(queryset.values(
        'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat_avg', 'score_heonbeob'))
    score_list_heonbeob = [s['score_heonbeob'] for s in score_list_all]
    score_list_eoneo = [s['score_eoneo'] for s in score_list_all]
    score_list_jaryo = [s['score_jaryo'] for s in score_list_all]
    score_list_sanghwang = [s['score_sanghwang'] for s in score_list_all]
    score_psat_avg = [s['score_psat_avg'] for s in score_list_all]

    top_score_heonbeob = get_top_score(score_list_heonbeob)
    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat_avg = get_top_score(score_psat_avg)

    try:
        stat_queryset['top_score_10_heonbeob'] = top_score_heonbeob[0]
        stat_queryset['top_score_20_heonbeob'] = top_score_heonbeob[1]

        stat_queryset['top_score_10_eoneo'] = top_score_eoneo[0]
        stat_queryset['top_score_20_eoneo'] = top_score_eoneo[1]

        stat_queryset['top_score_10_jaryo'] = top_score_jaryo[0]
        stat_queryset['top_score_20_jaryo'] = top_score_jaryo[1]

        stat_queryset['top_score_10_sanghwang'] = top_score_sanghwang[0]
        stat_queryset['top_score_20_sanghwang'] = top_score_sanghwang[1]

        stat_queryset['top_score_10_psat_avg'] = top_score_psat_avg[0]
        stat_queryset['top_score_20_psat_avg'] = top_score_psat_avg[1]
    except TypeError:
        pass

    return stat_queryset


def get_score_stat_korean(queryset) -> dict:
    stat_queryset = queryset.aggregate(
        응시_인원=Count('id'),

        헌법_최고_점수=Max('score_heonbeob', default=0),
        언어_최고_점수=Max('score_eoneo', default=0),
        자료_최고_점수=Max('score_jaryo', default=0),
        상황_최고_점수=Max('score_sanghwang', default=0),
        PSAT_최고_점수=Max('score_psat_avg', default=0),

        헌법_평균_점수=Avg('score_heonbeob', default=0),
        언어_평균_점수=Avg('score_eoneo', default=0),
        자료_평균_점수=Avg('score_jaryo', default=0),
        상황_평균_점수=Avg('score_sanghwang', default=0),
        PSAT_평균_점수=Avg('score_psat_avg', default=0),
    )

    score_list_all = list(queryset.values(
        'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat_avg', 'score_heonbeob'))
    score_list_heonbeob = [s['score_heonbeob'] for s in score_list_all]
    score_list_eoneo = [s['score_eoneo'] for s in score_list_all]
    score_list_jaryo = [s['score_jaryo'] for s in score_list_all]
    score_list_sanghwang = [s['score_sanghwang'] for s in score_list_all]
    score_psat_avg = [s['score_psat_avg'] for s in score_list_all]

    top_score_heonbeob = get_top_score(score_list_heonbeob)
    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat_avg = get_top_score(score_psat_avg)

    try:
        stat_queryset['헌법_상위_10%'] = top_score_heonbeob[0]
        stat_queryset['헌법_상위_20%'] = top_score_heonbeob[1]

        stat_queryset['언어_상위_10%'] = top_score_eoneo[0]
        stat_queryset['언어_상위_20%'] = top_score_eoneo[1]

        stat_queryset['자료_상위_10%'] = top_score_jaryo[0]
        stat_queryset['자료_상위_20%'] = top_score_jaryo[1]

        stat_queryset['상황_상위_10%'] = top_score_sanghwang[0]
        stat_queryset['상황_상위_20%'] = top_score_sanghwang[1]

        stat_queryset['PSAT_상위_10%'] = top_score_psat_avg[0]
        stat_queryset['PSAT_상위_20%'] = top_score_psat_avg[1]
    except TypeError:
        pass

    return stat_queryset


def get_all_score_stat_dict(get_statistics_qs, student) -> dict:
    stat_total = stat_department = None

    if student:
        stat_total = get_score_stat(get_statistics_qs('전체'))
        stat_department = get_score_stat(get_statistics_qs('직렬'))

    return {
        '전체': stat_total,
        '직렬': stat_department,
    }


def get_score_stat_sub(queryset) -> dict:
    score_stat_sub = {
        '헌법': {'sub': 'heonbeob'},
        '언어': {'sub': 'eoneo'},
        '자료': {'sub': 'jaryo'},
        '상황': {'sub': 'sanghwang'},
        '피셋': {'sub': 'psat'},
    }
    for key, item in score_stat_sub.items():
        item['num_students'] = None
        item['max_score'] = None
        item['avg_score'] = None
        item['top_score_10'] = None
        item['top_score_20'] = None
    stat_queryset = queryset.aggregate(
        num_students=Count('id'),

        max_score_heonbeob=Max('score_heonbeob', default=0),
        max_score_eoneo=Max('score_eoneo', default=0),
        max_score_jaryo=Max('score_jaryo', default=0),
        max_score_sanghwang=Max('score_sanghwang', default=0),
        max_score_psat_avg=Max('score_psat_avg', default=0),

        avg_score_heonbeob=Avg('score_heonbeob', default=0),
        avg_score_eoneo=Avg('score_eoneo', default=0),
        avg_score_jaryo=Avg('score_jaryo', default=0),
        avg_score_sanghwang=Avg('score_sanghwang', default=0),
        avg_score_psat_avg=Avg('score_psat_avg', default=0),
    )

    score_list_all = list(queryset.values(
        'score_eoneo', 'score_jaryo', 'score_sanghwang', 'score_psat_avg', 'score_heonbeob'))
    score_list_heonbeob = []
    score_list_eoneo = []
    score_list_jaryo = []
    score_list_sanghwang = []
    score_psat_avg = []
    for s in score_list_all:
        if s['score_heonbeob']:
            score_list_heonbeob.append(s['score_heonbeob'])
        if s['score_eoneo']:
            score_list_eoneo.append(s['score_eoneo'])
        if s['score_jaryo']:
            score_list_jaryo.append(s['score_jaryo'])
        if s['score_sanghwang']:
            score_list_sanghwang.append(s['score_sanghwang'])
        if s['score_psat_avg']:
            score_psat_avg.append(s['score_psat_avg'])
    # score_list_heonbeob = [s['score_heonbeob'] for s in score_list_all]
    # score_list_eoneo = [s['score_eoneo'] for s in score_list_all]
    # score_list_jaryo = [s['score_jaryo'] for s in score_list_all]
    # score_list_sanghwang = [s['score_sanghwang'] for s in score_list_all]
    # score_psat_avg = [s['score_psat_avg'] for s in score_list_all]

    top_score_heonbeob = get_top_score(score_list_heonbeob)
    top_score_eoneo = get_top_score(score_list_eoneo)
    top_score_jaryo = get_top_score(score_list_jaryo)
    top_score_sanghwang = get_top_score(score_list_sanghwang)
    top_score_psat_avg = get_top_score(score_psat_avg)

    for key, data in score_stat_sub.items():
        sub = data['sub']
        data['num_students'] = stat_queryset[f'num_students']
        if sub == 'psat':
            data['max_score'] = stat_queryset[f'max_score_psat_avg']
            data['avg_score'] = stat_queryset[f'avg_score_psat_avg']
        else:
            data['max_score'] = stat_queryset[f'max_score_{sub}']
            data['avg_score'] = stat_queryset[f'avg_score_{sub}']

    score_stat_sub['헌법']['top_score_10'] = top_score_heonbeob[0]
    score_stat_sub['헌법']['top_score_20'] = top_score_heonbeob[1]

    score_stat_sub['언어']['top_score_10'] = top_score_eoneo[0]
    score_stat_sub['언어']['top_score_20'] = top_score_eoneo[1]

    score_stat_sub['자료']['top_score_10'] = top_score_jaryo[0]
    score_stat_sub['자료']['top_score_20'] = top_score_jaryo[1]

    score_stat_sub['상황']['top_score_10'] = top_score_sanghwang[0]
    score_stat_sub['상황']['top_score_20'] = top_score_sanghwang[1]

    score_stat_sub['피셋']['top_score_10'] = top_score_psat_avg[0]
    score_stat_sub['피셋']['top_score_20'] = top_score_psat_avg[1]

    return score_stat_sub


def get_all_score_stat_sub_dict(get_statistics_qs, student) -> dict:
    stat_total = stat_department = None

    if student:
        stat_total = get_score_stat_sub(get_statistics_qs('전체'))
        stat_department = get_score_stat_sub(get_statistics_qs('직렬'))

    return {
        '전체': stat_total,
        '직렬': stat_department,
    }
