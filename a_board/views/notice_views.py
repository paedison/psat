import json

from django.contrib.auth.decorators import login_not_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django_htmx.http import retarget, reswap

from common.constants import icon_set_new
from common.utils import update_context_data, HtmxHttpRequest
from a_board import models, utils, forms


class NoticeConfiguration:
    menu = 'notice'
    info = {'menu': menu}
    title = {'kor': '공지사항', 'eng': menu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_board_notice_changelist')
    url_list = reverse_lazy(f'board:notice-list')
    url_create = reverse_lazy(f'board:notice-create')
    url = {'admin': url_admin, 'list': url_list, 'create': url_create}


@login_not_required
def list_view(request: HtmxHttpRequest):
    config = NoticeConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    queryset = utils.get_queryset(request, models.Notice)
    page_obj, page_range = utils.get_paginator_info(queryset, page_number)
    top_fixed = utils.get_filtered_queryset(request, models.Notice, top_fixed=True)
    context = update_context_data(
        config=config, icon_menu=icon_set_new.ICON_MENU['notice'], icon_board=icon_set_new.ICON_BOARD,
        page_obj=page_obj, page_range=page_range, top_fixed=top_fixed)
    if view_type == 'notice_list':
        return render(request, 'a_board/post_list_content.html', context)
    return render(request, 'a_board/post_list.html', context)


@login_not_required
def detail_view(request: HtmxHttpRequest, pk: int):
    config = NoticeConfiguration()
    queryset = utils.get_queryset(request, models.Notice)
    post: models.Notice = get_object_or_404(queryset, pk=pk)

    verified_list = json.loads(request.COOKIES.get('paedison_verified_list', '{}'))
    if 'notice' not in verified_list:
        verified_list['notice'] = []
    if pk not in verified_list['notice']:
        verified_list['notice'].append(pk)
        post.update_hit()

    prev_post, next_post = utils.get_prev_next_post(queryset, post)
    comments = models.NoticeComment.objects.filter(post=post)
    context = update_context_data(
        config=config, icon_menu=icon_set_new.ICON_MENU['notice'], icon_board=icon_set_new.ICON_BOARD,
        post=post, prev_post=prev_post, next_post=next_post, comments=comments)

    response = render(request, 'a_board/post_detail.html', context)
    response.set_cookie('paedison_verified_list', json.dumps(verified_list))
    return response


def create_view(request: HtmxHttpRequest):
    config = NoticeConfiguration()
    context = update_context_data(
        config=config, icon_menu=icon_set_new.ICON_MENU['notice'], icon_board=icon_set_new.ICON_BOARD)
    if request.method == 'POST':
        form = forms.NoticeForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect('board:notice-detail', pk=post.id)
    form = forms.NoticeForm()
    post_url = reverse_lazy('board:notice-create')
    context = update_context_data(context, form=form, post_url=post_url, message='등록')
    return render(request, 'a_board/post_create.html', context)


def update_view(request: HtmxHttpRequest, pk: int):
    config = NoticeConfiguration()
    instance = get_object_or_404(models.Notice, pk=pk)
    context = update_context_data(
        config=config, icon_menu=icon_set_new.ICON_MENU['notice'], icon_board=icon_set_new.ICON_BOARD)
    if request.method == 'POST':
        form = forms.NoticeForm(request.POST, instance=instance)
        if form.is_valid():
            notice = form.save()
            return redirect('board:notice-detail', pk=notice.id)
    form = forms.NoticeForm(instance=instance)
    context = update_context_data(context, form=form, post_url=instance.get_update_url(), message='수정')
    return render(request, 'a_board/post_create.html', context)


@require_POST
def delete_view(_, pk: int):
    instance = get_object_or_404(models.Notice, pk=pk)
    instance.delete()
    return redirect('board:notice-list')


@login_not_required
def comment_list_view(request: HtmxHttpRequest, post_id: int | None = None):
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')
    order_by = request.GET.get('order_by')

    if post_id is None:
        post_id = request.GET.get('post_id')
    post = get_object_or_404(models.Notice, pk=post_id)

    queryset = models.NoticeComment.objects.filter(post=post)
    if order_by == 'newest':
        queryset = queryset.order_by('-created_at')
    if order_by == 'oldest':
        queryset = queryset.order_by('created_at')
    comments, page_range = utils.get_paginator_info(queryset, page_number, per_page=5)
    pagination_url = post.get_comment_list_url()

    context = update_context_data(
        post=post, comments=comments, order_by=order_by,
        pagination_url=pagination_url, page_range=page_range)
    if view_type == 'pagination':
        response = render(request, 'a_board/comment_container.html#comment_box', context)
        return reswap(retarget(response, '#commentBox'), 'innerHTML swap:0.25s')
    return render(request, 'a_board/comment_container.html', context)


def comment_create_view(request: HtmxHttpRequest):
    form = forms.NoticeCommentCreateForm()

    if request.method == 'POST':
        form = forms.NoticeCommentCreateForm(data=request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = form.cleaned_data['post']
            comment.save()
            url = f"{reverse_lazy('board:notice-comment-list')}?post_id={comment.post.id}"
            return redirect(url)
        else:
            context = update_context_data(form=form)
            response = render(request, 'a_board/snippets/comment_form.html', context)
            return reswap(retarget(response, '#commentForm'), 'innerHTML swap:0.25s')

    context = update_context_data(form=form)
    return render(request, 'a_board/snippets/comment_form.html', context)


def comment_update_view(request: HtmxHttpRequest, pk: int):
    instance = get_object_or_404(models.NoticeComment, pk=pk)
    context = update_context_data(comment=instance)

    if request.method == 'POST':
        form = forms.NoticeCommentUpdateForm(data=request.POST, instance=instance)
        if form.is_valid():
            comment = form.save()
            url = f"{reverse_lazy('board:notice-comment-list')}?post_id={comment.post.id}"
            return redirect(url)
    else:
        form = forms.NoticeCommentUpdateForm(instance=instance)

    context = update_context_data(context, form=form)
    return render(request, 'a_board/snippets/comment_form.html', context)


@require_POST
def comment_delete_view(_, pk: int):
    comment = get_object_or_404(models.NoticeComment, pk=pk)
    post_id = comment.post_id
    url = f"{reverse_lazy('board:notice-comment-list')}?post_id={post_id}"
    comment.delete()
    return redirect(url)
