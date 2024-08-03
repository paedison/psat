__all__ = [
    'get_page_obj_and_range',
    'get_qs_student_for_admin_views', 'update_stat_page',
    'update_answer_page', 'update_catalog_page'
]

from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast

from a_predict.views.base_info import PredictExamVars


def get_page_obj_and_range(page_data, page_number=1, per_page=10):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None


def get_qs_student_for_admin_views(exam_vars, exam, qs_student, category):
    if category == 'filtered':
        qs_student = qs_student.filter(
            answer_all_confirmed_at__isnull=False, answer_all_confirmed_at__lte=exam.answer_official_opened_at)
    if exam_vars.is_psat:
        return qs_student.annotate(
            all_psat_rank=Cast(
                KeyTextTransform('psat_avg', KeyTextTransform(
                    'total', KeyTextTransform(category, 'rank'))),
                output_field=IntegerField(),
            ),
            zero_rank_order=Case(
                When(all_psat_rank=0, then=Value(1)), default=Value(0), output_field=IntegerField(),
            )
        ).order_by('zero_rank_order', 'all_psat_rank')
    return qs_student.annotate(
        all_rank=Cast(
            KeyTextTransform('sum', KeyTextTransform(
                'total', KeyTextTransform(category, 'rank'))),
            output_field=IntegerField(),
        ),
        zero_rank_order=Case(
            When(all_rank=0, then=Value(1)), default=Value(0), output_field=IntegerField(),
        )
    ).order_by('zero_rank_order', 'all_rank')


def update_stat_page(exam_vars: PredictExamVars, exam, page_obj, category: str):
    participants = exam.participants[category]
    statistics = exam.statistics[category]
    for idx, obj in enumerate(page_obj):
        obj_id = str(obj['id']) if isinstance(obj, dict) else str(obj.id)
        stat = []
        for fld in exam_vars.admin_score_fields:
            _participants = participants[obj_id][fld] if fld in participants[obj_id] else ''
            _max = statistics[obj_id][fld].get('max') if fld in statistics[obj_id] else ''
            _t10 = statistics[obj_id][fld].get('t10') if fld in statistics[obj_id] else ''
            _t20 = statistics[obj_id][fld].get('t20') if fld in statistics[obj_id] else ''
            _avg = statistics[obj_id][fld].get('avg') if fld in statistics[obj_id] else ''
            stat_dict = {
                'field': fld, 'participants': _participants,
                'max': _max, 't10': _t10, 't20': _t20, 'avg': _avg,
            }
            stat.append(stat_dict)
        if isinstance(obj, dict):
            obj['stat'] = stat
        else:
            obj.stat = stat


def update_catalog_page(exam_vars: PredictExamVars, exam, qs_department, page_obj, category):
    participants = exam.participants[category]
    departments = {department.name: str(department.id) for department in qs_department}
    for obj in page_obj:
        department_id = departments[obj.department]
        obj.stat = [{} for _ in exam_vars.admin_score_fields]

        for dt in obj.data:
            fld = dt[0]
            fld_idx = exam_vars.admin_score_fields.index(fld)
            _rank_total = obj.rank[category]['total'].get(fld, '')
            _rank_department = obj.rank[category]['department'].get(fld, '')
            _participants_total = participants['total'].get(fld, '')
            _participants_department = participants[department_id].get(fld, '')
            obj.stat[fld_idx].update({
                'field': fld,
                'score': dt[2],
                'rank_total': _rank_total,
                'rank_department': _rank_department,
                'participants_total': _participants_total,
                'participants_department': _participants_department,
            })


def update_answer_page(exam_vars: PredictExamVars, exam, answer_predict, page_obj):
    answer_official = exam.answer_official

    for obj in page_obj:
        no_idx = obj.number - 1
        fld = obj.subject
        fld_idx = exam_vars.get_field_idx(fld, admin=True)
        answer_count = getattr(obj, 'all')
        if fld in answer_official:
            ans_official = answer_official[fld][no_idx]
            obj.ans_official = ans_official
            obj.ans_predict = answer_predict[fld_idx][no_idx]['ans']
            for rnk in exam_vars.rank_list:
                ans_count = answer_count[rnk]
                rate = 0
                try:
                    if ans_count[-1]:
                        rate = round(ans_count[ans_official] * 100 / ans_count[-1], 1)
                except IndexError:
                    pass
                setattr(obj, rnk, ans_count)
                setattr(obj, f'rate_{rnk}', rate)
            setattr(obj, 'rate_gap', obj.rate_top_rank - obj.rate_low_rank)
