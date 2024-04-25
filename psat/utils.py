from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse_lazy

from psat.models import psat_data_models
from reference.models import psat_models


def get_url_options(page_number, keyword, exam_reference, custom_options):
    url_options = f'page={page_number}&keyword={keyword}'
    url_options = add_data_into_url_options(url_options, exam_reference)
    url_options = add_data_into_url_options(url_options, custom_options)
    return url_options


def get_problem_by_problem_id(problem_id):
    if problem_id:
        return (
            psat_models.PsatProblem.objects
            .only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=models.F('psat__year'),
                ex=models.F('psat__exam__abbr'),
                exam=models.F('psat__exam__name'),
                sub=models.F('psat__subject__abbr'),
                subject=models.F('psat__subject__name'),
            )
            .get(id=problem_id)
        )


def get_sub_title_by_psat(psat, exam_reference, end_string='기출문제') -> str:
    title_parts = []
    year, ex, sub = exam_reference['year'], exam_reference['ex'], exam_reference['sub']
    if psat:
        if year:  # year
            title_parts.append(f'{psat.year}년')
        if ex:  # ex
            title_parts.append(psat.exam.name)
        if sub:  # sub
            title_parts.append(psat.subject.name)
        if not year and not ex and not sub:  # all
            title_parts.append('전체')
    else:
        title_parts.append('전체')
    sub_title = f'{" ".join(title_parts)} {end_string}'
    return sub_title


def get_sub_title_by_problem(problem):
    return f'{problem.year}년 {problem.exam} {problem.subject} {problem.number}번'


def get_list_data(custom_data) -> list:
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


def get_max_order(data):
    if not data.exists():
        return 1
    else:
        current_max = data.aggregate(max_order=models.Max('order'))['max_order']
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


def get_problem_queryset():
    return (
        psat_models.PsatProblem.objects
        .only('id', 'psat_id', 'number', 'answer', 'question')
        .annotate(
            year=models.F('psat__year'),
            ex=models.F('psat__exam__abbr'),
            exam=models.F('psat__exam__name'),
            sub=models.F('psat__subject__abbr'),
            subject=models.F('psat__subject__name'))
        .order_by('-psat__year', 'id')
    )


def get_custom_data_like(user_id, queryset, values_list_keys):
    return (
        queryset.filter(likes__is_liked=True, likes__user_id=user_id)
        .annotate(is_liked=models.F('likes__is_liked'))
        .values(*values_list_keys, 'is_liked'))


def get_custom_data_rate(user_id, queryset, values_list_keys):
    return (
        queryset.filter(rates__isnull=False, rates__user_id=user_id)
        .annotate(rating=models.F('rates__rating'))
        .values(*values_list_keys, 'rating'))


def get_custom_data_solve(user_id, queryset, values_list_keys):
    return (
        queryset.filter(solves__isnull=False, solves__user_id=user_id)
        .annotate(
            user_answer=models.F('solves__answer'),
            is_correct=models.F('solves__is_correct'))
        .values(*values_list_keys, 'user_answer', 'is_correct'))


def get_custom_data_memo(user_id, queryset, values_list_keys):
    return (
        queryset.filter(memos__isnull=False, memos__user_id=user_id)
        .values(*values_list_keys))


def get_custom_data_tag(user_id, queryset, values_list_keys):
    return (
        queryset.filter(tags__isnull=False, tags__user_id=user_id)
        .values(*values_list_keys))


def get_custom_data_collection(user_id, queryset, values_list_keys):
    return (
        queryset.filter(
            collection_items__isnull=False,
            collection_items__collection__user_id=user_id,
            collection_items__is_active=True,
        )
        .values(*values_list_keys))


def get_custom_data_comment(user_id, queryset, values_list_keys):
    return (
        queryset.filter(comments__isnull=False, comments__user_id=user_id)
        .values(*values_list_keys))


def add_data_into_url_options(url_options, data: dict):
    for key, item in data.items():
        url_options += f'&{key}={item}'
    return url_options


def get_memo(user_id, problem_id):
    if user_id:
        return psat_data_models.Memo.objects.filter(user_id=user_id, problem_id=problem_id).first()


def get_my_tag(user_id, problem_id):
    if user_id:
        return psat_data_models.Tag.objects.filter(user_id=user_id, problem_id=problem_id).first()


def get_comments(user_id, problem_id):
    if user_id:
        return psat_data_models.Comment.objects.filter(problem_id=problem_id).values()


def get_filter_dict(find_filter: dict, update_filter: dict):
    create_filter = find_filter.copy()
    create_filter.update(update_filter)
    return {
        'find': find_filter,
        'update': update_filter,
        'create': create_filter,
    }


def update_or_create_instance_by_filter_dict(data_model, filter_dict: dict):
    try:
        instance = data_model.objects.get(**filter_dict['find'])
        for key, item in filter_dict['update'].items():
            setattr(instance, key, item)
        instance.save()
    except data_model.DoesNotExist:
        instance = data_model.objects.create(**filter_dict['create'])
    return instance


def make_log_instance_by_filter_dict(log_model, filter_dict: dict, data_instance):
    find_filter = filter_dict['find']
    create_filter = filter_dict['create']
    recent_log = log_model.objects.filter(**find_filter).order_by('-id').first()
    repetition = recent_log.repetition + 1 if recent_log else 1
    create_filter.update(
        {'repetition': repetition, 'data_id': data_instance.id}
    )
    log_model.objects.create(**create_filter)


def get_comment_qs():
    return (
        psat_data_models.Comment.objects
        .select_related(
            'user', 'problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
        .annotate(
            username=models.F('user__username'),
            year=models.F('problem__psat__year'),
            ex=models.F('problem__psat__exam__abbr'),
            exam=models.F('problem__psat__exam__name'),
            sub=models.F('problem__psat__subject__abbr'),
            subject=models.F('problem__psat__subject__name'),
            number=models.F('problem__number'),
        )
    )


def get_all_comments(queryset, problem_id=None):
    if problem_id:
        queryset = queryset.filter(problem_id=problem_id)
    parent_comments = queryset.filter(parent__isnull=True).order_by('-timestamp')
    child_comments = queryset.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
    all_comments = []
    for comment in parent_comments:
        all_comments.append(comment)
        all_comments.extend(child_comments.filter(parent=comment))
    return all_comments


def get_all_comments_of_parent_comment(queryset, parent_comment):
    queryset = queryset.filter(parent=parent_comment)
    child_comments = queryset.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
    all_comments = [parent_comment]
    for comment in child_comments:
        all_comments.append(comment)
    return all_comments


def get_instance_by_id(queryset, instance_id):
    if instance_id:
        return queryset.get(id=instance_id)
