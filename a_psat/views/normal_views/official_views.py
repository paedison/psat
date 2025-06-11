from django.contrib.auth.decorators import login_not_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_psat import models, forms
from a_psat.utils.official_utils import *
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'official'
    submenu_kor = '기출문제'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}
    url_admin = reverse_lazy('admin:a_psat_problem_changelist')
    url_list = reverse_lazy('psat:problem-list')


@login_not_required
def official_problem_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    list_data = NormalListData(request=request)
    context = update_context_data(
        config=config,
        icon_image=icon_set_new.ICON_IMAGE,
        keyword=list_data.keyword,
        sub_title=list_data.sub_title,
    )

    if list_data.view_type == 'problem_list':
        context = update_context_data(context, problem_context=list_data.get_problem_context())
        return render(request, 'a_psat/problem_list_content.html', context)

    context = update_context_data(
        context,
        form=list_data.filterset.form,
        collections=list_data.get_collections(),
        problem_context=list_data.get_problem_context()
    )
    return render(request, 'a_psat/problem_list.html', context)


@login_not_required
def official_problem_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', 'main')
    problem = get_object_or_404(models.Problem, pk=pk)
    config.url_admin = reverse_lazy(f'admin:a_psat_problem_change', args=[pk])

    detail_data = NormalDetailData(request=request, problem=problem)
    context = update_context_data(config=config, problem_id=pk, problem=detail_data.problem)

    template_nav = 'a_psat/snippets/navigation_container.html'
    template_nav_problem_list = f'{template_nav}#nav_problem_list'
    template_nav_other_list = f'{template_nav}#nav_other_list'

    if view_type == 'image':
        return render(request, 'a_psat/problem_detail.html#modal_image', context)  # noqa

    if view_type == 'problem_list':
        context = update_context_data(context, **detail_data.problem_data.get_problem_list_context())
        return render(request, template_nav_problem_list, context)

    if view_type == 'like_list':
        context = update_context_data(context, **detail_data.problem_data.get_like_list_context())
        return render(request, template_nav_other_list, context)

    if view_type == 'rate_list':
        context = update_context_data(context, **detail_data.problem_data.get_rate_list_context())
        return render(request, template_nav_other_list, context)

    if view_type == 'solve_list':
        context = update_context_data(context, **detail_data.problem_data.get_solve_list_context())
        return render(request, template_nav_other_list, context)

    if view_type == 'memo_list':
        context = update_context_data(context, **detail_data.problem_data.get_memo_list_context())
        return render(request, template_nav_other_list, context)

    if view_type == 'tag_list':
        context = update_context_data(context, **detail_data.problem_data.get_tag_list_context())
        return render(request, template_nav_other_list, context)

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
        prob_prev=detail_data.prob_prev,
        prob_next=detail_data.prob_next,

        # custom_data & forms
        custom_data=detail_data.custom_data,
        my_memo=detail_data.get_my_memo(),
        tags=detail_data.get_my_tags(),
        memo_form=forms.ProblemMemoForm(),
        # comment_form=forms.ProblemCommentForm(),
        # reply_form=forms.ProblemCommentForm(),
    )
    return render(request, 'a_psat/problem_detail.html', context)


@require_POST
def official_like_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)
    update_data = NormalUpdateData(request=request, problem=problem)
    return update_data.get_like_problem_response()


def official_rate_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    if request.method == 'POST':
        update_data = NormalUpdateData(request=request, problem=problem)
        rating = request.POST.get('rating')
        return update_data.get_rate_problem_response(rating)

    context = update_context_data(problem=problem)
    return render(request, 'a_psat/snippets/rate_modal.html', context)


@require_POST
def official_solve_problem(request: HtmxHttpRequest, pk: int):
    answer = request.POST.get('answer')
    problem = get_object_or_404(models.Problem, pk=pk)
    update_data = NormalUpdateData(request=request, problem=problem)
    context = update_context_data(**update_data.get_solve_problem_response_context(answer))
    return render(request, 'a_psat/snippets/solve_modal.html', context)


def official_memo_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)
    update_data = NormalUpdateData(request=request, problem=problem)
    context = update_context_data(problem=problem, icon_memo=icon_set_new.ICON_MEMO, icon_board=icon_set_new.ICON_BOARD)

    if update_data.view_type == 'create' and request.method == 'POST':
        create_form = forms.ProblemMemoForm(request.POST)
        if create_form.is_valid():
            my_memo = create_form.save(commit=False)
            my_memo.problem_id = pk
            my_memo.user = request.user
            my_memo.save()
            context = update_context_data(context, my_memo=my_memo)
            return render(request, 'a_psat/snippets/memo_container.html', context)

    latest_record = models.ProblemMemo.objects.filter(problem=problem, user=request.user, is_active=True).first()

    if update_data.view_type == 'update':
        if request.method == 'POST':
            update_form = forms.ProblemMemoForm(request.POST, instance=latest_record)
            if update_form.is_valid():
                content = update_form.cleaned_data['content']
                context = update_context_data(context, my_memo=update_data.get_my_memo(content))
                return render(request, 'a_psat/snippets/memo_container.html', context)
        else:
            update_base_form = forms.ProblemMemoForm(instance=latest_record)
            context = update_context_data(context, memo_form=update_base_form, my_memo=latest_record)
            return render(request, 'a_psat/snippets/memo_container.html#update_form', context)  # noqa

    blank_form = forms.ProblemMemoForm()
    context = update_context_data(context, memo_form=blank_form)
    if update_data.view_type == 'delete' and request.method == 'POST':
        latest_record.is_active = False
        latest_record.save()
        memo_url = reverse_lazy('psat:memo-problem', args=[pk])
        context = update_context_data(context, memo_url=memo_url)
        return render(request, 'a_psat/snippets/memo_container.html', context)

    context = update_context_data(context, my_memo=latest_record)
    return render(request, 'a_psat/snippets/memo_container.html', context)


@require_POST
def official_tag_problem(request: HtmxHttpRequest, pk: int):
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


def official_collection_list_view(request: HtmxHttpRequest):
    collections = []
    collection_ids = request.POST.getlist('collection')
    if collection_ids:
        for idx, pk in enumerate(collection_ids, start=1):
            collection = models.ProblemCollection.objects.get(pk=pk, is_active=True)
            collection.order = idx
            collection.save()
            collections.append(collection)
    else:
        collections = models.ProblemCollection.objects.user_collection(request.user)
    context = update_context_data(collections=collections)
    return render(request, 'a_psat/collection_list.html', context)


def official_collection_create(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')

    if view_type == 'create':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                create_new_collection(request, form)
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
                create_new_collection(request, form)
                return redirect('psat:collect-problem', pk=problem_id)
        else:
            problem_id = request.GET.get('problem_id')
            form = forms.ProblemCollectionForm()
            context = update_context_data(
                form=form, url=reverse_lazy('psat:collection-create'),
                header='create_in_modal', problem_id=problem_id, target='#modalContainer')
            return render(request, 'a_psat/snippets/collection_create.html', context)


def create_new_collection(request, form):
    my_collection = form.save(commit=False)
    collection_counts = models.ProblemCollection.objects.user_collection(request.user).count()
    my_collection.user = request.user
    my_collection.order = collection_counts + 1
    my_collection.save()


def official_collection_detail_view(request: HtmxHttpRequest, pk: int):
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
            collections = models.ProblemCollection.objects.user_collection(request.user)
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

    items = models.ProblemCollectionItem.objects.collection_item(collection)
    custom_data = get_custom_data(request.user)
    for it in items:
        get_custom_icons(it.problem, custom_data)

    context = update_context_data(collection=collection, custom_data=custom_data, items=items)
    return render(request, 'a_psat/snippets/collection_item_card.html', context)


def official_collect_problem(request: HtmxHttpRequest, pk: int):
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
        collections = models.ProblemCollection.objects.user_collection_for_modal(request.user, pk)
        context = update_context_data(problem_id=pk, collections=collections)
        return render(request, 'a_psat/snippets/collection_modal.html', context)


def official_annotate_problem(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    problem: models.Problem = get_object_or_404(models.Problem, pk=pk)
    detail_data = NormalDetailData(request=request, problem=problem)
    detail_data.process_image()
    context = update_context_data(config=config, problem_id=pk, problem=problem)
    return render(request, 'a_psat/problem_annotate.html', context)


# def official_comment_list_view(request: HtmxHttpRequest):
#     page_number = int(request.GET.get('page', 1))
#     comment_qs = (
#         models.ProblemComment.objects.select_related('user', 'problem')
#         .annotate(
#             username=F('user__username'),
#             year=F('problem__year'),
#             exam=F('problem__exam'),
#             subject=F('problem__subject'),
#             number=F('problem__number'),
#         )
#     )
#     all_comments = official_utils.get_all_comments(comment_qs)
#     comment_context = get_paginator_context(all_comments, page_number)
#     pagination_url = reverse_lazy('psat:comment-list')
#     context = update_context_data(
#         comment_context=comment_context, pagination_url=pagination_url,
#         form=forms.ProblemCommentForm(),
#         icon_board=icon_set_new.ICON_BOARD,
#         icon_question=icon_set_new.ICON_QUESTION,
#     )
#     return render(request, 'a_psat/comment_list.html', context)
#
#
# def official_comment_create(_: HtmxHttpRequest):
#     pass
#
#
# def official_comment_detail_view(_: HtmxHttpRequest, __: int):
#     pass
#
#
# def official_comment_problem_create(request: HtmxHttpRequest, pk: int):
#     problem = get_object_or_404(models.Problem, pk=pk)
#     reply_form = forms.ProblemCommentForm()
#
#     if request.method == 'POST':
#         form = forms.ProblemCommentForm(request.POST)
#         if form.is_valid():
#             comment = form.save(commit=False)
#
#             content = form.cleaned_data['content']
#             soup = bs(content, 'html.parser')
#             title = soup.get_text()[:20]
#
#             comment.problem = problem
#             comment.user = request.user
#             comment.title = title
#             comment.save()
#             context = update_context_data(comment=comment, problem=problem, reply_form=reply_form)
#             return render(request, 'a_psat/snippets/comment.html', context)  # noqa
#
#
# def official_comment_problem_update(request: HtmxHttpRequest, pk: int):
#     comment = get_object_or_404(models.ProblemComment, pk=pk)
#     if request.method == 'POST':
#         form = forms.ProblemCommentForm(request.POST, instance=comment)
#         if form.is_valid():
#             form.save()
#             return redirect('problemcomment-list')
#     else:
#         form = forms.ProblemCommentForm(instance=comment)
#     return render(request, 'problemcomment_form.html', {'form': form})  # noqa
#
#
# def official_comment_problem_delete(request: HtmxHttpRequest, pk: int):
#     comment = get_object_or_404(models.ProblemComment, pk=pk)
#     if request.method == 'POST':
#         comment.delete()
#         return redirect('problemcomment-list')
#     return render(request, 'problemcomment_confirm_delete.html', {'comment': comment})  # noqa
#
#
# def official_comment_problem(_: HtmxHttpRequest, __: int):
#     pass
