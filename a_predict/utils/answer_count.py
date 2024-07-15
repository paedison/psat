from collections import Counter


def get_all_count_dict(exam_vars: dict, total_answer_lists: dict) -> dict:
    problem_count = exam_vars['problem_count']
    all_count_dict: dict[str, list[dict[str, str | int]]] = {
        field: [
            {
                'year': exam_vars['year'], 'exam': exam_vars['exam'],
                'round': exam_vars['round'], 'subject': field, 'number': number, 'answer': 0,
                'count_1': 0, 'count_2': 0, 'count_3': 0, 'count_4': 0, 'count_5': 0,
                'count_0': 0, 'count_multiple': 0, 'count_total': 0,
            } for number in range(1, count + 1)
        ] for field, count in problem_count.items()
    }
    for field, answer_lists in total_answer_lists.items():
        p_count = problem_count[field]
        if answer_lists:
            distributions = [Counter() for _ in range(p_count)]
            for lst in answer_lists:
                for i, value in enumerate(lst):
                    if value > 5:
                        distributions[i]['count_multiple'] += 1
                    else:
                        distributions[i][value] += 1

            for idx, counter in enumerate(distributions):
                count_dict = {f'count_{i}': counter.get(i, 0) for i in range(6)}
                count_dict['count_multiple'] = counter.get('count_multiple', 0)
                count_total = sum(value for value in count_dict.values())
                count_dict['count_total'] = count_total
                all_count_dict[field][idx].update(count_dict)
    return all_count_dict


def get_total_answer_lists_by_category(exam_vars: dict, exam, qs_student):
    subject_fields = exam_vars['subject_fields']
    rank_list = exam_vars['rank_list']
    total_answer_lists_by_category: dict[str, dict[str, dict[str, list]]] = {
        'all': {rank: {field: [] for field in subject_fields} for rank in rank_list},
        'filtered': {rank: {field: [] for field in subject_fields} for rank in rank_list},
    }
    participants_all = exam.participants['all']['total']['psat_avg']
    participants_filtered = exam.participants['filtered']['total']['psat_avg']

    for student in qs_student:
        rank_all_student = student.rank['all']['total']['psat_avg']
        rank_filtered_student = student.rank['filtered']['total']['psat_avg']
        rank_ratio_all = rank_all_student / participants_all if participants_all else None
        rank_ratio_filtered = rank_filtered_student / participants_filtered if participants_filtered else None

        for field in subject_fields:
            if student.answer_confirmed[field]:
                ans_student = student.answer[field]
                top_rank_threshold = 0.27
                mid_rank_threshold = 0.73

                def append_answer(catgry: str, rank: str):
                    total_answer_lists_by_category[catgry][rank][field].append(ans_student)

                append_answer('all', 'all_rank')
                if rank_ratio_all and 0 <= rank_ratio_all <= top_rank_threshold:
                    append_answer('all', 'top_rank')
                elif rank_ratio_all and top_rank_threshold < rank_ratio_all <= mid_rank_threshold:
                    append_answer('all', 'mid_rank')
                elif rank_ratio_all and mid_rank_threshold < rank_ratio_all <= 1:
                    append_answer('all', 'low_rank')

                if student.answer_all_confirmed_at and student.answer_all_confirmed_at < exam.answer_official_opened_at:
                    append_answer('filtered', 'all_rank')
                    if rank_ratio_filtered and 0 <= rank_ratio_filtered <= top_rank_threshold:
                        append_answer('filtered', 'top_rank')
                    elif rank_ratio_filtered and top_rank_threshold < rank_ratio_filtered <= mid_rank_threshold:
                        append_answer('filtered', 'mid_rank')
                    elif rank_ratio_filtered and mid_rank_threshold < rank_ratio_filtered <= 1:
                        append_answer('filtered', 'low_rank')
    return total_answer_lists_by_category


def get_total_count_dict_by_category(exam_vars: dict, total_answer_lists: dict):
    problem_count = exam_vars['problem_count']
    rank_list = exam_vars['rank_list']

    total_count_dict: dict[str, list[dict[str, str | dict[str, list]]]] = {
        field: [
            {
                'year': exam_vars['year'], 'exam': exam_vars['exam'],
                'round': exam_vars['round'], 'subject': field, 'number': number,
                'all': {rank: [] for rank in rank_list},
                'filtered': {rank: [] for rank in rank_list},
            } for number in range(1, count + 1)
        ] for field, count in problem_count.items()
    }
    for category, value1 in total_answer_lists.items():
        for rank, value2 in value1.items():
            for field, answer_lists in value2.items():
                p_count = problem_count[field]
                if answer_lists:
                    distributions = [Counter() for _ in range(p_count)]
                    for lst in answer_lists:
                        for i, value in enumerate(lst):
                            if value > 5:
                                distributions[i]['count_multiple'] += 1
                            else:
                                distributions[i][value] += 1

                    for idx, counter in enumerate(distributions):
                        count_list = [counter.get(i, 0) for i in range(6)]
                        count_total = sum(count_list[1:])
                        count_list.extend([counter.get('count_multiple', 0), count_total])
                        total_count_dict[field][idx][category][rank] = count_list

    return total_count_dict
