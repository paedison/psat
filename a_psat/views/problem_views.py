from bs4 import BeautifulSoup as bs
from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.db.models import F, Case, When, BooleanField
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models, utils, forms, filters


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'problem'
    submenu_kor = '기출문제'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_psat_problem_changelist')
    url_list = reverse_lazy('psat:problem-list')


@login_not_required
def problem_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    exam_subject = request.GET.get('subject', '')
    page_number = request.GET.get('page', 1)
    keyword = request.POST.get('keyword', '') or request.GET.get('keyword', '')

    sub_title = utils.get_sub_title_by_psat(exam_year, exam_exam, exam_subject)

    if request.user.is_authenticated:
        filterset = filters.ProblemFilter(data=request.GET, request=request)
    else:
        filterset = filters.AnonymousProblemFilter(data=request.GET, request=request)

    custom_data = utils.get_custom_data(request.user)
    page_obj, page_range = utils.get_paginator_data(filterset.qs, page_number)
    for problem in page_obj:
        utils.get_custom_icons(problem, custom_data)
    context = update_context_data(
        config=config, sub_title=sub_title, form=filterset.form,
        icon_image=icon_set_new.ICON_IMAGE,
        keyword=keyword,
        custom_data=custom_data, page_obj=page_obj, page_range=page_range,
    )
    if view_type == 'problem_list':
        return render(request, 'a_psat/problem_list_content.html', context)

    if request.user.is_authenticated:
        collections = models.ProblemCollection.objects.filter(user=request.user).order_by('order')
    else:
        collections = []

    context = update_context_data(context, collections=collections)
    return render(request, 'a_psat/problem_list.html', context)


@login_not_required
def problem_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', 'main')
    queryset = models.Problem.objects.all()
    problem: models.Problem = get_object_or_404(queryset, pk=pk)
    config.url_admin = reverse_lazy(f'admin:a_psat_problem_change', args=[pk])
    user_id = request.user.id if request.user.is_authenticated else None

    utils.process_image(problem)
    context = update_context_data(config=config, problem_id=pk, problem=problem)

    problem_data = queryset.filter(psat__year=problem.psat.year, psat__exam=problem.psat.exam, subject=problem.subject)
    prob_prev, prob_next = utils.get_prev_next_prob(pk, problem_data)

    template_nav = 'a_psat/snippets/navigation_container.html'
    template_nav_problem_list = f'{template_nav}#nav_problem_list'
    template_nav_other_list = f'{template_nav}#nav_other_list'

    if view_type == 'image':
        return render(request, 'a_psat/problem_detail.html#modal_image', context)

    if view_type == 'problem_list':
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='', list_data=list_data, color='primary')
        return render(request, template_nav_problem_list, context)

    if view_type == 'like_list':
        problem_data = queryset.prefetch_related('likes').filter(
            likes__is_liked=True, likes__user_id=user_id, likes__is_active=True).annotate(
            is_liked=F('likes__is_liked'))
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='즐겨찾기 추가 문제', list_data=list_data, color='danger')
        return render(request, template_nav_other_list, context)

    if view_type == 'rate_list':
        problem_data = queryset.prefetch_related('rates').filter(
            rates__isnull=False, rates__user_id=user_id, rates__is_active=True).annotate(
            rating=F('rates__rating'))
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='난이도 선택 문제', list_data=list_data, color='warning')
        return render(request, template_nav_other_list, context)

    if view_type == 'solve_list':
        problem_data = queryset.prefetch_related('solves').filter(
            solves__isnull=False, solves__user_id=user_id, solves__is_active=True).annotate(
            user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='정답 확인 문제', list_data=list_data, color='success')
        return render(request, template_nav_other_list, context)

    if view_type == 'memo_list':
        problem_data = queryset.prefetch_related('memos').filter(
            memos__isnull=False, memos__user_id=user_id, memos__is_active=True)
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='메모 작성 문제', list_data=list_data, color='warning')
        return render(request, template_nav_other_list, context)

    if view_type == 'tag_list':
        problem_data = queryset.prefetch_related('tagged_problems').filter(
            tags__isnull=False, tagged_problems__user=request.user).distinct()
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='태그 작성 문제', list_data=list_data, color='primary')
        return render(request, template_nav_other_list, context)

    memo_form = forms.ProblemMemoForm()
    memo_url = reverse_lazy('psat:memo-problem', args=[pk])
    # reply_form = forms.ProblemCommentForm()
    # comment_form = forms.ProblemCommentForm()

    custom_data = utils.get_custom_data(request.user)
    utils.get_custom_icons(problem, custom_data)

    my_memo = None
    for dt in custom_data['memo']:
        if dt.problem_id == problem.id:
            my_memo = models.ProblemMemo.objects.filter(user=request.user, problem=problem).first()

    tags = []
    for dt in custom_data['tag']:
        if dt.content_object_id == problem.id:
            tags = models.ProblemTag.objects.filter(
                tagged_items__user=request.user,
                tagged_items__content_object=problem,
                tagged_items__is_active=True,
            ).values_list('name', flat=True)

    # page = int(request.GET.get('page', 1))
    # comment_qs = (
    #     models.ProblemComment.objects.select_related('user', 'problem')
    #     .annotate(
    #         username=F('user__username'),
    #         year=F('problem__year'),
    #         exam=F('problem__exam'),
    #         subject=F('problem__subject'),
    #         number=F('problem__number'),
    #     )
    # )
    # all_comments = utils.get_all_comments(comment_qs, pk)
    # page_obj, page_range = utils.get_page_obj_and_range(page, all_comments)
    # pagination_url = reverse_lazy('psat:comment-problem')

    context = update_context_data(
        context,
        # icons
        icon_menu=icon_set_new.ICON_MENU['psat'],
        icon_question=icon_set_new.ICON_QUESTION,
        icon_nav=icon_set_new.ICON_NAV,
        icon_board=icon_set_new.ICON_BOARD,
        icon_like_white=icon_set_new.ICON_LIKE['white'],
        icon_rate_white=icon_set_new.ICON_RATE['white'],
        icon_solve_white=icon_set_new.ICON_SOLVE['white'],
        icon_memo_white=icon_set_new.ICON_MEMO['white'],
        icon_tag_white=icon_set_new.ICON_TAG['white'],

        # navigation data
        prob_prev=prob_prev, prob_next=prob_next,

        # custom_data & forms
        custom_data=custom_data, my_memo=my_memo, tags=tags,
        memo_form=memo_form, memo_url=memo_url,
        # comment_form=comment_form, reply_form=reply_form,
    )
    return render(request, 'a_psat/problem_detail.html', context)


@require_POST
def like_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)
    new_record = utils.create_new_custom_record(request, problem, models.ProblemLike)
    icon_like = icon_set_new.ICON_LIKE[f'{new_record.is_liked}']
    return HttpResponse(f'{icon_like}')


def rate_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        _ = utils.create_new_custom_record(
            request, problem, models.ProblemRate, **{'rating': rating})
        icon_rate = icon_set_new.ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    context = update_context_data(problem=problem)
    return render(request, 'a_psat/snippets/rate_modal.html', context)


@require_POST
def solve_problem(request: HtmxHttpRequest, pk: int):
    answer = request.POST.get('answer')
    problem = get_object_or_404(models.Problem, pk=pk)

    is_correct = None
    if answer:
        answer = int(answer)
        is_correct = answer == problem.answer
        _ = utils.create_new_custom_record(
            request, problem, models.ProblemSolve, **{'answer': answer, 'is_correct': is_correct})
    context = update_context_data(
        problem=problem, answer=answer, is_correct=is_correct,
        icon_solve=icon_set_new.ICON_SOLVE[f'{is_correct}'])

    return render(request, 'a_psat/snippets/solve_modal.html', context)


def memo_problem(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    context = update_context_data(
        problem=problem, icon_memo=icon_set_new.ICON_MEMO, icon_board=icon_set_new.ICON_BOARD)

    if view_type == 'create' and request.method == 'POST':
        create_form = forms.ProblemMemoForm(request.POST)
        if create_form.is_valid():
            my_memo = create_form.save(commit=False)
            my_memo.problem_id = pk
            my_memo.user = request.user
            my_memo.save()
            context = update_context_data(context, my_memo=my_memo)
            return render(request, 'a_psat/snippets/memo_container.html', context)

    latest_record = models.ProblemMemo.objects.filter(problem=problem, user=request.user, is_active=True).first()

    if view_type == 'update':
        if request.method == 'POST':
            update_form = forms.ProblemMemoForm(request.POST, instance=latest_record)
            if update_form.is_valid():
                content = update_form.cleaned_data['content']
                my_memo = utils.create_new_custom_record(
                    request, problem, models.ProblemMemo, **{'content': content})
                context = update_context_data(context, my_memo=my_memo)
                return render(request, 'a_psat/snippets/memo_container.html', context)
        else:
            update_base_form = forms.ProblemMemoForm(instance=latest_record)
            context = update_context_data(context, memo_form=update_base_form, my_memo=latest_record)
            return render(request, 'a_psat/snippets/memo_container.html#update_form', context)

    blank_form = forms.ProblemMemoForm()
    context = update_context_data(context, memo_form=blank_form)
    if view_type == 'delete' and request.method == 'POST':
        latest_record.is_active = False
        latest_record.save()
        memo_url = reverse_lazy('psat:memo-problem', args=[pk])
        context = update_context_data(context, memo_url=memo_url)
        return render(request, 'a_psat/snippets/memo_container.html', context)

    context = update_context_data(context, my_memo=latest_record)
    return render(request, 'a_psat/snippets/memo_container.html', context)


@require_POST
def tag_problem(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    name = request.POST.get('tag')
    base_info = {'content_object': problem, 'user': request.user, 'is_active': True}

    if view_type == 'add':
        tag, _ = models.ProblemTag.objects.get_or_create(name=name)
        models.ProblemTaggedItem.objects.create(tag=tag, **base_info)

    if view_type == 'remove':
        tagged_problem = get_object_or_404(models.ProblemTaggedItem, tag__name=name, **base_info)
        tagged_problem.is_active = False
        tagged_problem.save()

    is_tagged = models.ProblemTaggedItem.objects.filter(**base_info).exists()
    icon_tag = icon_set_new.ICON_TAG[f'{is_tagged}']
    return HttpResponse(icon_tag)


def collection_list_view(request: HtmxHttpRequest):
    collections = []
    collection_ids = request.POST.getlist('collection')
    if collection_ids:
        for idx, pk in enumerate(collection_ids, start=1):
            collection = models.ProblemCollection.objects.get(pk=pk, is_active=True)
            collection.order = idx
            collection.save()
            collections.append(collection)
    else:
        collections = models.ProblemCollection.objects.filter(user=request.user, is_active=True).order_by('order')
    context = update_context_data(collections=collections)
    return render(request, 'a_psat/collection_list.html', context)


def collection_create(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')

    if view_type == 'create':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                utils.create_new_collection(request, form)
                return redirect('psat:collection-list')
        else:
            form = forms.ProblemCollectionForm()
            context = update_context_data(form=form, url=reverse_lazy('psat:collection-create'), header='create')
            return render(request, 'a_psat/snippets/collection_create.html', context)

    if view_type == 'create_in_modal':
        if request.method == 'POST':
            problem_id = request.POST.get('problem_id')
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                utils.create_new_collection(request, form)
                return redirect('psat:collect-problem', pk=problem_id)
        else:
            problem_id = request.GET.get('problem_id')
            form = forms.ProblemCollectionForm()
            context = update_context_data(
                form=form, url=reverse_lazy('psat:collection-create'),
                header='create_in_modal', problem_id=problem_id, target='#modalContainer')
            return render(request, 'a_psat/snippets/collection_create.html', context)


def collection_detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    collection = get_object_or_404(models.ProblemCollection, pk=pk, is_active=True)

    if view_type == 'update':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST, instance=collection)
            if form.is_valid():
                form.save()
                return redirect('psat:collection-list')
        else:
            form = forms.ProblemCollectionForm(instance=collection)
            context = update_context_data(
                form=form, url=reverse_lazy('psat:collection-detail', args=[pk]), header='update')
            return render(request, 'a_psat/snippets/collection_create.html', context)

    if view_type == 'delete':
        with transaction.atomic():
            collection.order = 0
            collection.is_active = False
            collection.save()
            collections = models.ProblemCollection.objects.filter(user=request.user, is_active=True).order_by('order')
            if collections:
                for idx, col in enumerate(collections, start=1):
                    col.order = idx
                    col.save()
        return redirect('psat:collection-list')

    item_pks = request.POST.getlist('item')
    if item_pks:
        with transaction.atomic():
            for idx, item_pk in enumerate(item_pks, start=1):
                item = get_object_or_404(models.ProblemCollectionItem, pk=item_pk, is_active=True)
                item.order = idx
                item.save()

    items = models.ProblemCollectionItem.objects.filter(collection=collection, is_active=True).order_by('order')
    custom_data = utils.get_custom_data(request.user)
    for it in items:
        utils.get_custom_icons(it.problem, custom_data)

    context = update_context_data(collection=collection, custom_data=custom_data, items=items)
    return render(request, 'a_psat/snippets/collection_item_card.html', context)


def collect_problem(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(models.ProblemCollection, id=collection_id, is_active=True)

        base_info = {'collection': collection, 'is_active': True}
        items = models.ProblemCollectionItem.objects.filter(**base_info).order_by('order')

        is_checked = request.POST.get('is_checked')
        if is_checked:
            models.ProblemCollectionItem.objects.create(problem_id=pk, order=items.count() + 1, **base_info)
        else:
            with transaction.atomic():
                item = get_object_or_404(models.ProblemCollectionItem, problem_id=pk, **base_info)
                item.order = 0
                item.is_active = False
                item.save()
                if items:
                    for idx, it in enumerate(items, start=1):
                        it.order = idx
                        it.save()
        is_active = models.ProblemCollectionItem.objects.filter(
            collection__user=request.user, problem_id=pk, is_active=True).exists()
        return HttpResponse(icon_set_new.ICON_COLLECTION[f'{is_active}'])

    else:
        collection_ids = models.ProblemCollectionItem.objects.filter(
            collection__user=request.user, problem_id=pk, is_active=True,
        ).values_list('collection_id', flat=True).distinct()
        item_exists = Case(When(id__in=collection_ids, then=1), default=0, output_field=BooleanField())
        collections = models.ProblemCollection.objects.filter(
            user=request.user, is_active=True).order_by('order').annotate(item_exists=item_exists)
        context = update_context_data(problem_id=pk, collections=collections)
        return render(request, 'a_psat/snippets/collection_modal.html', context)


def annotate_problem(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    problem: models.Problem = get_object_or_404(models.Problem, pk=pk)
    utils.process_image(problem)
    context = update_context_data(config=config, problem_id=pk, problem=problem)
    return render(request, 'a_psat/problem_annotate.html', context)


def comment_list_view(request: HtmxHttpRequest):
    page_number = int(request.GET.get('page', 1))
    comment_qs = (
        models.ProblemComment.objects.select_related('user', 'problem')
        .annotate(
            username=F('user__username'),
            year=F('problem__year'),
            exam=F('problem__exam'),
            subject=F('problem__subject'),
            number=F('problem__number'),
        )
    )
    all_comments = utils.get_all_comments(comment_qs)
    page_obj, page_range = utils.get_paginator_data(all_comments, page_number)
    pagination_url = reverse_lazy('psat:comment-list')
    context = update_context_data(
        page_obj=page_obj, page_range=page_range, pagination_url=pagination_url,
        form=forms.ProblemCommentForm(),
        icon_board=icon_set_new.ICON_BOARD,
        icon_question=icon_set_new.ICON_QUESTION,
    )
    return render(request, 'a_psat/comment_list.html', context)


def comment_create(request: HtmxHttpRequest):
    pass


def comment_detail_view(request: HtmxHttpRequest, pk: int):
    pass


def comment_problem_create(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)
    reply_form = forms.ProblemCommentForm()

    if request.method == 'POST':
        form = forms.ProblemCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)

            content = form.cleaned_data['content']
            soup = bs(content, 'html.parser')
            title = soup.get_text()[:20]

            comment.problem = problem
            comment.user = request.user
            comment.title = title
            comment.save()
            context = update_context_data(comment=comment, problem=problem, reply_form=reply_form)
            return render(request, 'a_psat/snippets/comment.html', context)


def comment_problem_update(request: HtmxHttpRequest, pk: int):
    comment = get_object_or_404(models.ProblemComment, pk=pk)
    if request.method == 'POST':
        form = forms.ProblemCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('problemcomment-list')
    else:
        form = forms.ProblemCommentForm(instance=comment)
    return render(request, 'problemcomment_form.html', {'form': form})


def comment_problem_delete(request: HtmxHttpRequest, pk: int):
    comment = get_object_or_404(models.ProblemComment, pk=pk)
    if request.method == 'POST':
        comment.delete()
        return redirect('problemcomment-list')
    return render(request, 'problemcomment_confirm_delete.html', {'comment': comment})


def comment_problem(request: HtmxHttpRequest, pk: int):
    pass
