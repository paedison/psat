from a_predict.models import OfficialAnswer, StudentAnswer

SUBJECTS = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang']


def get_dict_answer(qs):
    dict_answer = {}
    for sub in SUBJECTS:
        answer_string = getattr(qs, sub)
        if answer_string:
            answer_list = answer_string.split(",")
            dict_answer[sub] = []
            for number, ans in enumerate(answer_list, 1):
                if ans == '' or isinstance(ans, int):
                    ans = ans
                else:
                    ans = int(ans)
                ans_list = [int(a) for a in str(ans) if ans > 5]
                append_dict = {'no': number, 'ans': ans}
                if ans_list:
                    append_dict['ans_list'] = ans_list
                dict_answer[sub].append(append_dict)
    return dict_answer


def run():
    qs_official_answers = OfficialAnswer.objects.all()
    update_list = []
    for qs in qs_official_answers:
        qs.answer = get_dict_answer(qs)
        update_list.append(qs)

    OfficialAnswer.objects.bulk_update(
        update_list, ['answer']
    )
    print(f'{len(update_list)} OfficialAnswer objects successfully updated.')
