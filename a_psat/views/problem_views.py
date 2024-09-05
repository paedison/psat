from bs4 import BeautifulSoup as bs
from django.contrib.auth.decorators import login_not_required
from django.db.models import F, Max, Case, When, BooleanField, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_psat import models, utils, forms, filters
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data


class ProblemConfiguration:
    menu = 'psat'
    submenu = 'problem'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': 'PSAT', 'eng': menu.capitalize()}
    submenu_title = {'kor': '기출문제', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_psat_problem_changelist')
    url_list = reverse_lazy(f'psat:problem-list')
    icon_menu = icon_set_new.ICON_MENU[menu]


@login_not_required
def problem_list_view(request: HtmxHttpRequest):
    config = ProblemConfiguration()
    view_type = request.headers.get('View-Type', '')
    exam_year = request.GET.get('year', '')
    exam_exam = request.GET.get('exam', '')
    exam_subject = request.GET.get('subject', '')
    page = request.GET.get('page', '1')

    sub_title = utils.get_sub_title_by_psat(exam_year, exam_exam, exam_subject)

    if request.user.is_authenticated:
        filterset = filters.PsatFilter(data=request.GET, request=request)
    else:
        filterset = filters.AnonymousPsatFilter(data=request.GET, request=request)

    custom_data = utils.get_custom_data(request.user)
    page_obj, page_range = utils.get_page_obj_and_range(page, filterset.qs)
    for problem in page_obj:
        utils.get_custom_icons(problem, custom_data)
    context = update_context_data(
        config=config, sub_title=sub_title, form=filterset.form,
        icon_menu=icon_set_new.ICON_MENU['psat'], icon_image=icon_set_new.ICON_IMAGE,
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
    config = ProblemConfiguration()
    view_type = request.headers.get('View-Type', 'main')
    queryset = models.Problem.objects.order_by('-year', 'id')
    problem: models.Problem = get_object_or_404(queryset, pk=pk)
    config.url_admin = reverse_lazy(f'admin:a_psat_problem_change', args=[pk])
    user_id = request.user.id if request.user.is_authenticated else None

    context = update_context_data(config=config, problem_id=pk, problem=problem)

    problem_data = queryset.filter(year=problem.year, exam=problem.exam, subject=problem.subject)
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
            likes__is_liked=True, likes__user_id=user_id).annotate(is_liked=F('likes__is_liked'))
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='즐겨찾기 추가 문제', list_data=list_data, color='danger')
        return render(request, template_nav_other_list, context)

    if view_type == 'rate_list':
        problem_data = queryset.prefetch_related('rates').filter(
            rates__isnull=False, rates__user_id=user_id).annotate(rating=F('rates__rating'))
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='난이도 선택 문제', list_data=list_data, color='warning')
        return render(request, template_nav_other_list, context)

    if view_type == 'solve_list':
        problem_data = queryset.prefetch_related('solves').filter(
            solves__isnull=False, solves__user_id=user_id).annotate(
            user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
        list_data = utils.get_list_data(problem_data)
        context = update_context_data(context, list_title='정답 확인 문제', list_data=list_data, color='success')
        return render(request, template_nav_other_list, context)

    if view_type == 'memo_list':
        problem_data = queryset.prefetch_related('memos').filter(memos__isnull=False, memos__user_id=user_id)
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
                tagged_items__active=True,
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
    problem_like, created = models.ProblemLike.objects.get_or_create(user=request.user, problem=problem)
    is_liked = True
    if not created:
        is_liked = not problem_like.is_liked
        problem_like.is_liked = is_liked
        message_type = 'liked' if is_liked else 'unliked'
        problem_like.save(message_type=message_type)
    icon_like = icon_set_new.ICON_LIKE[f'{is_liked}']
    return HttpResponse(f'{icon_like}')


def rate_problem(request: HtmxHttpRequest, pk: int):
    problem = get_object_or_404(models.Problem, pk=pk)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        problem_rate = models.ProblemRate.objects.filter(user=request.user, problem=problem)
        if problem_rate:
            problem_rate = problem_rate.first()
            problem_rate.rating = rating
            problem_rate.save(message_type='rerated')
        else:
            models.ProblemRate.objects.create(user=request.user, problem=problem, rating=rating)
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
        problem_solve = models.ProblemSolve.objects.filter(problem=problem, user=request.user)
        if problem_solve:
            problem_solve = problem_solve.first()
            problem_solve.answer = answer
            problem_solve.is_correct = is_correct
            problem_solve.save()
        else:
            models.ProblemSolve.objects.create(
                problem=problem, user=request.user, answer=answer, is_correct=is_correct)
    context = update_context_data(
        problem=problem, answer=answer, is_correct=is_correct,
        icon_solve=icon_set_new.ICON_SOLVE[f'{is_correct}'])

    return render(request, 'a_psat/snippets/solve_modal.html', context)


def memo_problem(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    instance = models.ProblemMemo.objects.filter(problem=problem, user=request.user).first()
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

    if view_type == 'update':
        if request.method == 'POST':
            update_form = forms.ProblemMemoForm(request.POST, instance=instance)
            if update_form.is_valid():
                my_memo = update_form.save()
                context = update_context_data(context, my_memo=my_memo)
                return render(request, 'a_psat/snippets/memo_container.html', context)
        else:
            update_base_form = forms.ProblemMemoForm(instance=instance)
            context = update_context_data(context, memo_form=update_base_form, my_memo=instance)
            return render(request, 'a_psat/snippets/memo_container.html#update_form', context)

    blank_form = forms.ProblemMemoForm()
    context = update_context_data(context, memo_form=blank_form)
    if view_type == 'delete' and request.method == 'POST':
        instance.delete()
        memo_url = reverse_lazy('psat:memo-problem', args=[pk])
        context = update_context_data(context, memo_url=memo_url)
        return render(request, 'a_psat/snippets/memo_container.html', context)

    context = update_context_data(context, my_memo=instance)
    return render(request, 'a_psat/snippets/memo_container.html', context)


@require_POST
def tag_problem(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    problem = get_object_or_404(models.Problem, pk=pk)
    name = request.POST.get('tag')

    if view_type == 'add':
        tag, _ = models.ProblemTag.objects.get_or_create(name=name)
        tagged_problem, created = models.ProblemTaggedItem.objects.get_or_create(
            user=request.user, content_object=problem, tag=tag)
        if not created:
            tagged_problem.active = True
            tagged_problem.save(message_type='tagged')

    if view_type == 'remove':
        tagged_problem = get_object_or_404(
            models.ProblemTaggedItem, user=request.user, content_object=problem, tag__name=name)
        tagged_problem.active = False
        tagged_problem.save(message_type='removed')

    is_tagged = models.ProblemTaggedItem.objects.filter(
        user=request.user, content_object=problem, active=True).exists()
    icon_tag = icon_set_new.ICON_TAG[f'{is_tagged}']
    html_code = f'<span hx-swap-oob="innerHTML:#dailyTag{problem.id}">{icon_tag}</span>'
    return HttpResponse(html_code)


def collection_list_view(request: HtmxHttpRequest):
    collections = []
    collection_ids = request.POST.getlist('collection')
    if collection_ids:
        for idx, pk in enumerate(collection_ids, start=1):
            collection = models.ProblemCollection.objects.get(pk=pk)
            collection.order = idx
            collection.save()
            collections.append(collection)
    else:
        collections = models.ProblemCollection.objects.filter(user=request.user)
    context = update_context_data(collections=collections)
    return render(request, 'a_psat/collection_list.html', context)


def collection_create(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', '')

    if view_type == 'create':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                my_collection = form.save(commit=False)
                existing_collections = models.ProblemCollection.objects.filter(user=request.user)
                max_order = 1
                if existing_collections:
                    max_order = existing_collections.aggregate(max_order=Max('order'))['max_order'] + 1
                my_collection.user = request.user
                my_collection.order = max_order
                my_collection.save()
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
                my_collection = form.save(commit=False)
                existing_collections = models.ProblemCollection.objects.filter(user=request.user)
                max_order = 1
                if existing_collections:
                    max_order = existing_collections.aggregate(max_order=Max('order'))['max_order'] + 1
                my_collection.user = request.user
                my_collection.order = max_order
                my_collection.save()
                return redirect('psat:collect-problem', pk=problem_id)
        else:
            problem_id = request.GET.get('problem_id')
            form = forms.ProblemCollectionForm()
            context = update_context_data(
                form=form, url=reverse_lazy('psat:collection-create'),
                header='create_in_modal', problem_id=problem_id,
                target='#modalContainer'
            )
            return render(request, 'a_psat/snippets/collection_create.html', context)


def collection_detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    collection = get_object_or_404(models.ProblemCollection, pk=pk)

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
        collection.delete()
        collections = models.ProblemCollection.objects.filter(user_id=request.user.id)
        if collections:
            for idx, col in enumerate(collections, start=1):
                col.order = idx
                col.save()
        return redirect('psat:collection-list')

    item_ids = request.POST.getlist('item')
    if item_ids:
        for idx, item_pk in enumerate(item_ids, start=1):
            item = models.ProblemCollectionItem.objects.select_related('problem').get(pk=item_pk)
            item.order = idx
            item.save()
    items = models.ProblemCollectionItem.objects.filter(collection=collection)
    custom_data = utils.get_custom_data(request.user)
    context = update_context_data(collection=collection, items=items, custom_data=custom_data)
    return render(request, 'a_psat/snippets/collection_item_card.html', context)


def collect_problem(request: HtmxHttpRequest, pk: int):
    if request.method == 'POST':
        collection_id = request.POST.get('collection_id')
        collection = get_object_or_404(models.ProblemCollection, id=collection_id)
        is_checked = request.POST.get('is_checked')

        max_order = models.ProblemCollectionItem.objects.filter(
            collection=collection).aggregate(
            max_order=Coalesce(Max('order'), Value(0)))['max_order'] + 1

        if is_checked:
            item = models.ProblemCollectionItem.objects.create(
                collection=collection, problem_id=pk, order=max_order)
        else:
            item = get_object_or_404(models.ProblemCollectionItem, collection=collection, problem_id=pk)
            item.delete()
            items = models.ProblemCollectionItem.objects.filter(collection=collection)
            if items:
                for idx, it in enumerate(items, start=1):
                    it.order = idx
                    it.save()
        is_active = True if item else False
        return HttpResponse(icon_set_new.ICON_COLLECTION[f'{is_active}'])

    else:
        collection_ids = models.ProblemCollectionItem.objects.filter(
            collection__user_id=request.user.id, problem_id=pk
        ).values_list('collection_id', flat=True).distinct()
        item_exists_case = Case(
            When(id__in=collection_ids, then=1), default=0, output_field=BooleanField())
        collections = models.ProblemCollection.objects.filter(
            user_id=request.user.id).annotate(item_exists=item_exists_case)
        context = update_context_data(problem_id=pk, collections=collections)
        return render(request, 'a_psat/snippets/collection_modal.html', context)


def comment_list_view(request: HtmxHttpRequest):
    page = int(request.GET.get('page', 1))
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
    page_obj, page_range = utils.get_page_obj_and_range(page, all_comments)
    pagination_url = reverse_lazy('psat:comment-list')
    context = update_context_data(
        page_obj=page_obj, page_range=page_range, pagination_url=pagination_url,
        form=forms.ProblemCommentForm(),
        icon_board=icon_set_new.ICON_BOARD,
        icon_question=icon_set_new.ICON_QUESTION,
    )
    return render(request, 'a_psat/comment_list.html', context)


def comment_create(request: HtmxHttpRequest):
    view_type = request.headers.get('View-Type', 'main')

    if view_type == 'create':
        if request.method == 'POST':
            form = forms.ProblemCollectionForm(request.POST)
            if form.is_valid():
                my_collection = form.save(commit=False)
                existing_collections = models.ProblemCollection.objects.filter(user=request.user)
                max_order = 1
                if existing_collections:
                    max_order = existing_collections.aggregate(max_order=Max('order'))['max_order'] + 1
                my_collection.user = request.user
                my_collection.order = max_order
                my_collection.save()
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
                my_collection = form.save(commit=False)
                existing_collections = models.ProblemCollection.objects.filter(user=request.user)
                max_order = 1
                if existing_collections:
                    max_order = existing_collections.aggregate(max_order=Max('order'))['max_order'] + 1
                my_collection.user = request.user
                my_collection.order = max_order
                my_collection.save()
                return redirect('psat:collect-problem', pk=problem_id)
        else:
            problem_id = request.GET.get('problem_id')
            form = forms.ProblemCollectionForm()
            context = update_context_data(
                form=form, url=reverse_lazy('psat:collection-create'),
                header='create_in_modal', problem_id=problem_id,
                target='#modalContainer'
            )
            return render(request, 'a_psat/snippets/collection_create.html', context)


def comment_detail_view(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    collection = get_object_or_404(models.ProblemCollection, pk=pk)

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
        collection.delete()
        collections = models.ProblemCollection.objects.filter(user_id=request.user.id)
        if collections:
            for idx, col in enumerate(collections, start=1):
                col.order = idx
                col.save()
        return redirect('psat:collection-list')

    item_ids = request.POST.getlist('item')
    if item_ids:
        for idx, item_pk in enumerate(item_ids, start=1):
            item = models.ProblemCollectionItem.objects.select_related('problem').get(pk=item_pk)
            item.order = idx
            item.save()
    items = models.ProblemCollectionItem.objects.filter(collection=collection)
    custom_data = utils.get_custom_data(request.user)
    context = update_context_data(collection=collection, items=items, custom_data=custom_data)
    return render(request, 'a_psat/snippets/collection_item_card.html', context)


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
    comment = get_object_or_404(ProblemComment, pk=pk)
    if request.method == 'POST':
        form = ProblemCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('problemcomment-list')
    else:
        form = ProblemCommentForm(instance=comment)
    return render(request, 'problemcomment_form.html', {'form': form})


def comment_problem_delete(request: HtmxHttpRequest, pk: int):
    comment = get_object_or_404(ProblemComment, pk=pk)
    if request.method == 'POST':
        comment.delete()
        return redirect('problemcomment-list')
    return render(request, 'problemcomment_confirm_delete.html', {'comment': comment})


def comment_problem(request: HtmxHttpRequest, pk: int):
    pass
