from django.core.paginator import Paginator
from django.db.models import Max, F
from django.urls import reverse_lazy

from reference.models import psat_models


def get_max_order(data):
    if not data.exists():
        return 1
    else:
        current_max = data.aggregate(max_order=Max('order'))['max_order']
        return current_max + 1


def get_new_ordering(data):
    if not data.exists():
        return
    number_of_data = data.count()
    new_ordering = range(1, number_of_data+1)
    return new_ordering


def get_page_obj_and_range(page_number, page_data, per_page):
    paginator = Paginator(page_data, per_page)
    try:
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range
    except TypeError:
        return None, None


def get_url(name, *args):
    if args:
        base_url = reverse_lazy(f'psat:{name}', args=[*args])
        return f'{base_url}?'
    base_url = reverse_lazy(f'psat:{name}')
    return f'{base_url}?'


def get_list_data(custom_data) -> list:
    def get_view_list_data():
        organized_dict = {}
        organized_list = []
        for prob in custom_data:
            key = prob['psat_id']
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam, subject = prob['year'], prob['exam'], prob['subject']
            problem_url = reverse_lazy('psat:detail', args=[prob['id']])
            list_item = {
                'exam_name': f"{year}년 {exam} {subject}",
                'problem_number': prob['number'],
                'problem_id': prob['id'],
                'problem_url': problem_url
            }
            organized_dict[key].append(list_item)

        for key, items in organized_dict.items():
            num_empty_instances = 5 - (len(items) % 5)
            if num_empty_instances < 5:
                items.extend([None] * num_empty_instances)
            for i in range(0, len(items), 5):
                row = items[i:i+5]
                organized_list.extend(row)
        return organized_list
    return get_view_list_data()


def get_problem_from_problem_id(problem_id):
    if problem_id:
        return (
            psat_models.PsatProblem.objects
            .only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .get(id=problem_id)
        )


def get_problem_queryset():
    return (
        psat_models.PsatProblem.objects
        .only('id', 'psat_id', 'number', 'answer', 'question')
        .annotate(
            year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
            sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
        .order_by('-psat__year', 'id')
    )
