__all__ = [
    'get_page_obj_and_range',
    'get_qs_student_for_admin_views', 'update_stat_page',
    'update_answer_page', 'update_catalog_page'
]


from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField
from django.db.models.fields.json import KeyTextTransform

from a_predict.views.base_info import PredictExamVars


def get_page_obj_and_range(page_data, page_number=1, per_page=10):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None


def get_qs_student_for_admin_views(qs_student, category):
    if category == 'filtered':
        qs_student = qs_student.filter(answer_all_confirmed_at__isnull=False)
    return qs_student.annotate(
        all_psat_rank=KeyTextTransform('psat_avg', KeyTextTransform(
            'total', KeyTextTransform(category, 'rank'))),
        zero_rank_order=Case(
            When(all_psat_rank=0, then=Value(1)),
            default=Value(0), output_field=IntegerField(),
        )
    ).order_by('zero_rank_order', 'all_psat_rank')


def update_stat_page(exam_vars: PredictExamVars, exam, page_obj, category: str):
    participants = exam.participants[category]
    statistics = exam.statistics[category]
    for idx, obj in enumerate(page_obj):
        obj_id = obj['id'] if isinstance(obj, dict) else str(obj.id)
        stat = []
        for fld in exam_vars.score_fields:
            stat_dict = {
                'participants': participants[obj_id][fld],
                'max': statistics[obj_id][fld].get('max'),
                't10': statistics[obj_id][fld].get('t10'),
                't20': statistics[obj_id][fld].get('t20'),
                'avg': statistics[obj_id][fld].get('avg'),
            }
            stat.append(stat_dict)
        if isinstance(obj, dict):
            obj['stat'] = stat
        else:
            obj.stat = stat


def update_catalog_page(exam_vars: PredictExamVars, exam, qs_department, page_obj, category):
    participants = exam.participants[category]
    departments = {
        department.name: str(department.id) for department in qs_department
    }
    for obj in page_obj:
        department_id = departments[obj.department]
        obj.stat = []
        for idx, fld in enumerate(exam_vars.score_fields):
            obj.stat.append({
                'score': obj.data[idx][2],
                'rank_total': obj.rank[category]['total'][fld],
                'rank_department': obj.rank[category]['department'][fld],
                'participants_total': participants['total'][fld],
                'participants_department': participants[department_id][fld],
            })


def update_answer_page(exam_vars: PredictExamVars, exam, answer_predict, page_obj):
    answer_official = exam.answer_official

    for obj in page_obj:
        no = obj.number
        fld = obj.subject
        fld_idx = exam_vars.get_field_idx(fld)
        answer_count = getattr(obj, 'all')
        if fld in answer_official:
            ans_official = answer_official[fld][no - 1]

            obj.ans_official = ans_official
            obj.ans_predict = answer_predict[fld_idx][no - 1]['ans']
            for fld in exam_vars.rank_list:
                rate = 0
                try:
                    if answer_count[fld][-1]:
                        rate = round(
                            answer_count[fld][ans_official] * 100 / answer_count[fld][-1], 1
                        )
                except IndexError:
                    pass
                setattr(obj, fld, answer_count[fld])
                setattr(obj, f'rate_{fld}', rate)
            setattr(obj, 'rate_gap', obj.rate_top_rank - obj.rate_low_rank)
