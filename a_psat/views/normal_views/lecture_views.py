from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from a_psat import models, forms
from a_psat.utils.lecture_utils import NormalDetailData
from common.constants import icon_set_new
from common.utils import Configuration, HtmxHttpRequest, update_context_data


class ViewConfiguration(Configuration):
    menu_eng, menu_kor = 'psat', 'PSAT'
    submenu_eng, submenu_kor = 'lecture', '온라인강의'
    url_list = reverse_lazy('psat:lecture-list')


def lecture_list_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    lectures = models.Lecture.objects.order_by_subject_code()
    context = update_context_data(config=config, lectures=lectures, icon_menu=icon_set_new.ICON_MENU['psat'])
    return render(request, 'a_psat/lecture_list.html', context)


def lecture_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    lecture = get_object_or_404(models.Lecture, pk=pk)
    detail_data = NormalDetailData(request=request, lecture=lecture)

    context = update_context_data(
        config=config,
        icon_nav=icon_set_new.ICON_NAV,
        lecture=lecture,
        lecture_list=detail_data.lecture_list,
        prev_lec=detail_data.prev_lec,
        next_lec=detail_data.next_lec,
        lec_images=detail_data.get_lecture_images(),
        memo_form=forms.LectureMemoForm(),
        memo_url=reverse_lazy('psat:memo-lecture', args=[pk]),
        my_memo=models.LectureMemo.objects.my_memo(request.user, lecture),
        tags=models.LectureTag.objects.my_tags(request.user, lecture),
    )
    return render(request, 'a_psat/lecture_detail.html', context)


def memo_lecture(request: HtmxHttpRequest, pk: int):
    view_type = request.headers.get('View-Type', '')
    lecture = get_object_or_404(models.Lecture, pk=pk)
    context = update_context_data(lecture=lecture, icon_memo=icon_set_new.ICON_MEMO, icon_board=icon_set_new.ICON_BOARD)

    if view_type == 'create' and request.method == 'POST':
        create_form = forms.LectureMemoForm(request.POST)
        if create_form.is_valid():
            my_memo = create_form.save(commit=False)
            my_memo.lecture_id = pk
            my_memo.user = request.user
            my_memo.save()
            context = update_context_data(context, my_memo=my_memo)
            return render(request, 'a_psat/snippets/memo_container.html', context)

    latest_record = models.LectureMemo.objects.filter(lecture=lecture, user=request.user).first()

    if view_type == 'update':
        if request.method == 'POST':
            update_form = forms.LectureMemoForm(request.POST, instance=latest_record)
            if update_form.is_valid():
                my_memo = update_form.save()
                context = update_context_data(context, my_memo=my_memo)
                return render(request, 'a_psat/snippets/memo_container.html', context)
        else:
            update_base_form = forms.LectureMemoForm(instance=latest_record)
            context = update_context_data(context, memo_form=update_base_form, my_memo=latest_record)
            return render(request, 'a_psat/snippets/memo_container.html#update_form', context)  # noqa

    blank_form = forms.LectureMemoForm()
    context = update_context_data(context, memo_form=blank_form)
    if view_type == 'delete' and request.method == 'POST':
        latest_record.delete()
        memo_url = reverse_lazy('psat:memo-lecture', args=[pk])
        context = update_context_data(context, memo_url=memo_url)
        return render(request, 'a_psat/snippets/memo_container.html', context)

    context = update_context_data(context, my_memo=latest_record)
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
