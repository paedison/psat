from a_predict.models import OfficialAnswer, StatisticsVirtual

SUBJECTS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']


def run():
    qs_statistics_virtual = StatisticsVirtual.objects.all()
    update_list = []
    for qs in qs_statistics_virtual:
        dict_score = {}
        psat_score = 0
        for sub in SUBJECTS:
            score = getattr(qs, f'score_{sub}')
            if score:
                dict_score[sub] = getattr(qs, f'score_{sub}')
                psat_score += score

        if psat_score:
            dict_score['psat_avg'] = psat_score / 3

        qs.score = dict_score
        update_list.append(qs)

    StatisticsVirtual.objects.bulk_update(update_list, ['score'])
    print(f'{len(update_list)} StatisticsVirtual objects successfully updated.')
