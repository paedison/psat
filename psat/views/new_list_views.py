from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import reverse_lazy

from common import constants
from .list_views import get_evaluation_info
from ..filters import PsatProblemFilter
from ..models import Problem, Exam

menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET


def problem(request):
    template_name = 'psat/new_problem_list.html#content' if request.htmx else 'psat/new_problem_list.html'
    view_type = 'problem'
    problem_filter = PsatProblemFilter(request.GET, queryset=Problem.objects.all())
    base_url = reverse_lazy('psat:new_problem_list')

    year = request.GET.get('exam__year', '')
    ex = request.GET.get('exam__ex', '')
    sub = request.GET.get('exam__sub', '')
    pagination_url = f'{base_url}?exam__year={year}&exam__ex={ex}&exam__sub={sub}'

    exam_objects = Exam.objects.all()
    if year:
        exam_objects = exam_objects.filter(year=year)
    if ex:
        exam_objects = exam_objects.filter(ex=ex)
    if sub:
        exam_objects = exam_objects.filter(sub=sub)

    year_list_raw = exam_objects.values_list('year', flat=True).distinct()
    year_list = []
    for y in year_list_raw:
        year_list.append((f'{y}', f'{y}년'))

    ex_list_raw = exam_objects.values_list('ex', 'exam2')
    ex_list = []
    for e in ex_list_raw:
        if e not in ex_list:
            ex_list.append(e)

    sub_list_raw = exam_objects.values_list('sub', 'subject')
    sub_list = []
    for s in sub_list_raw:
        if s not in sub_list:
            sub_list.append(s)

    # Get paginator for total exam list
    paginate_by = 10
    paginator = Paginator(problem_filter.qs, paginate_by)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(
        number=page_number, on_each_side=3, on_ends=1)

    for obj in page_obj:
        get_evaluation_info(request.user, obj)

    info = {
        'menu': view_type,
        'view_type': view_type,
        'type': f'{view_type}List',
        'title': 'PSAT 기출문제',
        'pagination_url': pagination_url,
        'icon': menu_icon_set[view_type],
        'color': color_set[view_type],
    }

    context = {
        'info': info,
        'form': problem_filter.form,
        'page_obj': page_obj,
        'page_range': page_range,
        'pagination_url': pagination_url,
        'problem_list': True,
        'year': year,
        'ex': ex,
        'sub': sub,
        'year_list': year_list,
        'ex_list': ex_list,
        'sub_list': sub_list,
    }
    return render(request, template_name, context)
