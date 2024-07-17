def update_stat_page(exam_vars, exam, page_obj, category: str):
    admin_score_fields = exam_vars.admin_score_fields
    participants = exam.participants[category]
    statistics = exam.statistics[category]
    for obj in page_obj:
        try:
            obj_id = str(obj.id)
            obj.stat = []
        except AttributeError:
            obj_id = str(obj['id'])
            obj['stat'] = []

        for field in admin_score_fields:
            stat_dict = {
                'participants': participants[obj_id][field],
                'max': statistics[obj_id][field].get('max'),
                't10': statistics[obj_id][field].get('t10'),
                't20': statistics[obj_id][field].get('t20'),
                'avg': statistics[obj_id][field].get('avg'),
            }
            try:
                obj.stat.append(stat_dict)
            except AttributeError:
                obj['stat'].append(stat_dict)


def update_answer_page(exam_vars, exam, page_obj, answer_predict):
    subject_fields = exam_vars.subject_fields
    rank_list = exam_vars.rank_list

    for obj in page_obj:
        no = obj.number
        field = obj.subject
        field_idx = subject_fields.index(field)
        answer_count = getattr(obj, 'all')
        ans_official = exam.answer_official[field][no - 1]

        obj.ans_official = ans_official
        obj.ans_predict = answer_predict[field_idx][no - 1]['ans']
        for field in rank_list:
            rate = round(
                answer_count[field][ans_official] * 100 / answer_count[field][-1], 1
            )
            setattr(obj, field, answer_count[field])
            setattr(obj, f'rate_{field}', rate)
        setattr(obj, 'rate_gap', obj.rate_top_rank - obj.rate_low_rank)


def update_admin_catalog_page(exam_vars, exam, qs_department, page_obj, category):
    admin_catalog_fields = exam_vars.admin_score_fields
    participants = exam.participants[category]

    departments = {
        department.name: str(department.id) for department in qs_department
    }

    for obj in page_obj:
        department_id = departments[obj.department]
        obj.stat = []
        for field in admin_catalog_fields:
            rank_total = obj.rank[category]['total'][field]
            rank_department = obj.rank[category]['department'][field]
            participants_total = participants['total'][field]
            participants_department = participants[department_id][field]
            rank_ratio_total = round(rank_total * 100 / participants_total, 1)
            rank_ratio_department = round(rank_department * 100 / participants_department, 1)
            obj.stat.append({
                'score': obj.score[field],
                'rank_total': rank_total,
                'rank_department': rank_department,
                'rank_ratio_total': rank_ratio_total,
                'rank_ratio_department': rank_ratio_department,
            })
