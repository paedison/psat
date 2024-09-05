import vanilla

from .viewmixins import lecture_view_mixins
from a_psat import models, utils, forms, filters
from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST


class LectureConfiguration:
    menu = 'psat'
    submenu = 'lecture'
    info = {'menu': menu, 'menu_self': submenu}
    menu_title = {'kor': 'PSAT', 'eng': menu.capitalize()}
    submenu_title = {'kor': '온라인강의', 'eng': submenu.capitalize()}
    url_admin = reverse_lazy(f'admin:a_psat_lecture_changelist')
    url_list = reverse_lazy(f'psat:lecture-list')
    icon_menu = icon_set_new.ICON_MENU[menu]


def lecture_list_view(request: HtmxHttpRequest):
    config = LectureConfiguration()
    lectures = models.Lecture.objects.order_by_subject_code()
    context = update_context_data(
        config=config, lectures=lectures, icon_menu=icon_set_new.ICON_MENU['psat'])
    return render(request, 'a_psat/lecture_list.html', context)


def lecture_detail_view(request: HtmxHttpRequest, pk: int):
    config = LectureConfiguration()
    queryset = models.Lecture.objects.order_by_subject_code()
    lecture: models.Lecture = get_object_or_404(queryset, pk=pk)
    prev_lec, next_lec = utils.get_prev_next_prob(pk, queryset)
    lec_images = utils.get_lecture_images(lecture)

    memo_form = forms.LectureMemoForm()
    memo_url = reverse_lazy('psat:memo-lecture', args=[pk])
    custom_data = utils.get_memo_custom_data(request.user)

    my_memo = None
    for dt in custom_data['memo']:
        if dt.lecture_id == lecture.id:
            my_memo = models.LectureMemo.objects.filter(user=request.user, lecture=lecture).first()

    tags = []
    for dt in custom_data['tag']:
        if dt.content_object_id == lecture.id:
            tags = models.LectureTag.objects.filter(
                tagged_items__user=request.user,
                tagged_items__content_object=lecture,
                tagged_items__active=True,
            ).values_list('name', flat=True)

    context = update_context_data(
        config=config, lecture=lecture, lec_images=lec_images,
        prev_lec=prev_lec, next_lec=next_lec, icon_nav=icon_set_new.ICON_NAV,
        memo_form=memo_form, my_memo=my_memo, memo_url=memo_url, tags=tags,
    )
    return render(request, 'a_psat/lecture_detail.html', context)


def memo_lecture(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    lecture = get_object_or_404(models.Lecture, pk=pk)
    instance = models.LectureMemo.objects.filter(lecture=lecture, user=request.user).first()
    context = update_context_data(
        lecture=lecture, icon_memo=icon_set_new.ICON_MEMO, icon_board=icon_set_new.ICON_BOARD)

    if view_type == 'create' and request.method == 'POST':
        create_form = forms.LectureMemoForm(request.POST)
        if create_form.is_valid():
            my_memo = create_form.save(commit=False)
            my_memo.lecture_id = pk
            my_memo.user = request.user
            my_memo.save()
            context = update_context_data(context, my_memo=my_memo)
            return render(request, 'a_psat/snippets/memo_container.html', context)

    if view_type == 'update':
        if request.method == 'POST':
            update_form = forms.LectureMemoForm(request.POST, instance=instance)
            if update_form.is_valid():
                my_memo = update_form.save()
                context = update_context_data(context, my_memo=my_memo)
                return render(request, 'a_psat/snippets/memo_container.html', context)
        else:
            update_base_form = forms.LectureMemoForm(instance=instance)
            context = update_context_data(context, memo_form=update_base_form, my_memo=instance)
            return render(request, 'a_psat/snippets/memo_container.html#update_form', context)

    blank_form = forms.LectureMemoForm()
    context = update_context_data(context, memo_form=blank_form)
    if view_type == 'delete' and request.method == 'POST':
        instance.delete()
        memo_url = reverse_lazy('psat:memo-lecture', args=[pk])
        context = update_context_data(context, memo_url=memo_url)
        return render(request, 'a_psat/snippets/memo_container.html', context)

    context = update_context_data(context, my_memo=instance)
    return render(request, 'a_psat/snippets/memo_container.html', context)


@require_POST
def tag_lecture(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    lecture = get_object_or_404(models.Lecture, pk=pk)
    name = request.POST.get('tag', '')

    if view_type == 'add':
        tag, _ = models.LectureTag.objects.get_or_create(name=name)
        tagged_lecture, created = models.LectureTaggedItem.objects.get_or_create(
            user=request.user, content_object=lecture, tag=tag)
        if not created:
            tagged_lecture.active = True
            tagged_lecture.save(message_type='tagged')

    if view_type == 'remove':
        tagged_lecture = get_object_or_404(
            models.LectureTaggedItem, user=request.user, content_object=lecture, tag__name=name)
        tagged_lecture.active = False
        tagged_lecture.save(message_type='untagged')

    return HttpResponse('')
