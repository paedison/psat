from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from ..forms import PrimePsatStudentForm
from ..models import PrimePsatExam, PrimePsatStudent, PrimePsatRegisteredStudent, PrimePsatAnswerCount
from ..utils import get_tuple_data_answer_official_student, get_dict_stat_data, get_dict_frequency_score


def list_view(request: HtmxHttpRequest):
    info = {
        'menu': 'score',
        'view_type': 'primeScore',
    }
    exam_list = PrimePsatExam.objects.all()

    page_number = request.GET.get('page', 1)
    paginator = Paginator(exam_list, 10)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)

    if request.user.is_authenticated:
        for obj in page_obj:
            student = PrimePsatStudent.objects.filter(
                registered_students__user=request.user, year=obj.year, round=obj.round).first()
            if student:
                obj.student = student
                obj.student_score = student.score
                obj.detail_url = reverse_lazy(
                    'score_prime_psat:detail',
                    kwargs={'exam_year': obj.year, 'exam_round': obj.round})

    context = update_context_data(
        # base info
        info=info,
        title='Score',
        sub_title='프라임 PSAT 모의고사 성적표',
        current_time=timezone.now(),

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,

        # page objectives
        page_obj=page_obj,
        page_range=page_range,
    )

    if request.htmx:
        return render(request, 'a_score/prime_list.html#list_main', context)
    return render(request, 'a_score/prime_list.html', context)


def detail_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    if not request.user.is_authenticated:
        return redirect('score_prime_psat:list')

    student = PrimePsatStudent.objects.filter(
        year=exam_year, round=exam_round, registered_students__user=request.user).first()
    if not student:
        return redirect('score_prime_psat:list')

    info = {
        'menu': 'score',
        'view_type': 'primeScore',
    }

    exam = get_object_or_404(PrimePsatExam, year=exam_year, round=exam_round)
    qs_answer_count = PrimePsatAnswerCount.objects.filter(
        year=exam_year, round=exam_round).order_by('subject', 'number')
    data_answer_official, data_answer_student = get_tuple_data_answer_official_student(
        student, exam, qs_answer_count)

    stat_total = get_dict_stat_data(student=student, statistics_type='total')
    stat_department = get_dict_stat_data(student=student, statistics_type='department')

    frequency_score = get_dict_frequency_score(student)

    context = update_context_data(
        # base info
        info=info,
        exam_year=exam_year,
        exam_round=exam_round,
        title='Score',
        sub_title=f'제{exam_round}회 프라임 PSAT 모의고사',

        # icons
        icon_menu=icon_set_new.ICON_MENU['score'],
        icon_subject=icon_set_new.ICON_SUBJECT,
        icon_nav=icon_set_new.ICON_NAV,

        # info_student: 수험 정보
        student=student,

        # sheet_score: 성적 확인
        stat_total=stat_total,
        stat_department=stat_department,

        # chart: 성적 분포 차트
        frequency_score=frequency_score,

        # sheet_answer: 답안 확인
        data_answer_official=data_answer_official,
        data_answer_student=data_answer_student,
    )

    if request.htmx:
        return render(request, 'a_score/prime_detail.html#detail_main', context)
    return render(request, 'a_score/prime_detail.html', context)


def detail_print_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    pass


def no_open_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    exam = get_object_or_404(PrimePsatExam, year=exam_year, round=exam_round)
    context = update_context_data(exam=exam)
    return render(request, 'a_score/snippets/prime_no_open_modal.html', context)


def no_student_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    context = update_context_data(exam_year=exam_year, exam_round=exam_round)
    return render(request, 'a_score/snippets/prime_no_student_modal.html', context)


@login_required
def student_connect_modal_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    header = f'{exam_year}년 대비 제{exam_round}회 프라임 모의고사 수험 정보 입력'
    url_kwargs = {'exam_year': exam_year, 'exam_round': exam_round}
    url_detail = reverse_lazy('score_prime_psat:detail', kwargs=url_kwargs)
    url_student_connect = reverse_lazy('score_prime_psat:student_connect', kwargs=url_kwargs)
    context = update_context_data(
        header=header, exam_year=exam_year, exam_round=exam_round,
        url_detail=url_detail, url_student_connect=url_student_connect)
    return render(request, 'a_score/snippets/prime_student_connect_modal.html', context)


def no_predict_open_modal(request: HtmxHttpRequest):
    context = update_context_data(
    )
    return render(request, 'a_score/snippets/prime_no_open_modal.html', context)


@login_required
def student_connect_view(request: HtmxHttpRequest, exam_year: int, exam_round: int):
    form = PrimePsatStudentForm()
    context = update_context_data(form=form, exam_year=exam_year, exam_round=exam_round)
    if request.method == "POST":
        form = PrimePsatStudentForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form = form.save(commit=False)
            target_student = PrimePsatStudent.objects.get(
                year=exam_year,
                round=exam_round,
                serial=form.serial,
                name=form.name,
                password=form.password,
            )
            registered_student, _ = PrimePsatRegisteredStudent.objects.get_or_create(
                user=request.user, student=target_student
            )
            context = update_context_data(context, form=form, user_verified=True)
        else:
            context = update_context_data(context, form=form)

    return render(request, 'a_score/snippets/prime_student_connect_modal.html#student_info', context)


@login_required
def student_reset_view(request: HtmxHttpRequest):
    context = update_context_data(
    )
    return render(request, 'a_score/snippets/prime_no_open_modal.html', context)

# def index_view(request: HtmxHttpRequest):
#     ei = ExamInfo()
#     exam = ei.qs_exam.first()
#
#     if not request.user.is_authenticated:
#         return render(request, 'a_score/index.html', {})
#
#     student = ei.get_obj_student(request=request)
#     if not student:
#         return redirect('predict:student-create')
#
#     info = {
#         'menu': 'predict',
#         'view_type': 'predict',
#     }
#
#     data_answer_official = ei.get_dict_data_answer_official(exam=exam)
#     qs_answer_count = ei.qs_answer_count
#     data_answer_rate = ei.get_dict_data_answer_rate(
#         data_answer_official=data_answer_official,
#         qs_answer_count=qs_answer_count,
#     )
#
#     data_answer_student, data_answer_count, data_answer_confirmed = (
#         ei.get_tuple_data_answer_student(request=request, data_answer_rate=data_answer_rate)
#     )
#     data_answer_predict = ei.get_dict_data_answer_predict(
#         data_answer_official=data_answer_official,
#         qs_answer_count=qs_answer_count,
#     )
#
#     info_answer_student = ei.get_dict_info_answer_student(
#         data_answer_student=data_answer_student,
#         data_answer_count=data_answer_count,
#         data_answer_confirmed=data_answer_confirmed,
#         data_answer_official=data_answer_official,
#         data_answer_predict=data_answer_predict,
#     )
#
#     stat_total_all = ei.get_dict_stat_data(student=student, statistics_type='total')
#     stat_department_all = ei.get_dict_stat_data(student=student, statistics_type='department')
#     stat_total_filtered = ei.get_dict_stat_data(
#         student=student, statistics_type='total', exam=exam)
#     stat_department_filtered = ei.get_dict_stat_data(
#         student=student, statistics_type='department', exam=exam)
#
#     context = update_context_data(
#         # base info
#         info=info,
#         exam=exam,
#         current_time=timezone.now(),
#
#         # icons
#         icon_menu=icon_set_new.ICON_MENU['predict'],
#         icon_subject=icon_set_new.ICON_SUBJECT,
#         icon_nav=icon_set_new.ICON_NAV,
#
#         # index_info_student: 수험 정보
#         student=student,
#         location=ei.get_obj_location(student=student),
#
#         # index_info_answer: 답안 제출 현황
#         info_answer_student=info_answer_student,
#
#         # index_sheet_answer: 답안 확인
#         data_answer_official=data_answer_official,
#         data_answer_predict=data_answer_predict,
#         data_answer_student=data_answer_student,
#
#         # index_sheet_score: 성적 예측 I [전체 데이터]
#         stat_total_all=stat_total_all,
#         stat_department_all=stat_department_all,
#
#         # index_sheet_score_filtered: 성적 예측 II [정답 공개 전 데이터]
#         stat_total_filtered=stat_total_filtered,
#         stat_department_filtered=stat_department_filtered,
#     )
#     return render(request, 'a_score/index.html', context)
#
#
# @login_required
# def student_create_view(request: HtmxHttpRequest):
#     ei = ExamInfo()
#     student = ei.get_obj_student(request=request)
#     if student:
#         return redirect('predict:index')
#
#     if request.method == "POST":
#         form = predict_forms.StudentForm(request.POST)
#         if form.is_valid():
#             student = form.save(commit=False)
#             ei.create_student(student=student, request=request)
#         else:
#             pass
#         first_sub = '헌법' if '헌법' in ei.PROBLEM_COUNT.keys() else '언어'
#         return redirect('predict:answer-input', first_sub)
#
#     else:
#         form = predict_forms.StudentForm()
#
#     units = ei.qs_unit.values_list('unit', flat=True)
#     context = update_context_data(
#         # base info
#         info=ei.INFO,
#         exam=ei.EXAM,
#         current_time=timezone.now(),
#
#         # icons
#         icon_menu=icon_set_new.ICON_MENU['predict'],
#         icon_subject=icon_set_new.ICON_SUBJECT,
#         icon_nav=icon_set_new.ICON_NAV,
#
#         # index_info_student: 수험 정보
#         units=units,
#         form=form,
#     )
#
#     return render(request, 'a_score/student_create.html', context)
#
#
# # @login_required
# def department_list(request):
#     if request.method == 'POST':
#         ei = ExamInfo()
#         unit = request.POST.get('unit')
#         departments = ei.qs_department.filter(unit=unit).values_list('department', flat=True)
#         context = update_context_data(departments=departments)
#         return render(request, 'a_score/snippets/department_list.html', context)
#
#
# # @login_required
# def answer_input_view(request, sub):
#     ei = ExamInfo()
#
#     if sub not in ei.PROBLEM_COUNT.keys():
#         return redirect('predict:index')
#
#     student = ei.get_obj_student(request=request)
#     if not student:
#         return redirect('predict:student-create')
#
#     field = ei.SUBJECT_VARS[sub][1]
#     is_confirmed = ei.get_obj_student_answer(request=request).answer_confirmed[field]
#     if is_confirmed:
#         return redirect('predict:index')
#
#     answer_student_list = ei.get_list_answer_temp(request=request, sub=sub)
#
#     context = update_context_data(
#         info=ei.INFO, exam=ei.EXAM, sub=sub, answer_student=answer_student_list)
#     return render(request, 'a_score/answer_input.html', context)
#
#
# @login_required
# def answer_submit(request, sub):
#     if request.method == 'POST':
#         ei = ExamInfo()
#         submitted_answer = ei.create_submitted_answer(request, sub)
#         context = update_context_data(sub=sub, submitted_answer=submitted_answer)
#         return render(request, 'a_score/snippets/submitted_answer_form.html', context)
#
#
# @login_required
# def answer_confirm(request, sub):
#     if request.method == 'POST':
#         ei = ExamInfo()
#         subject, field = ei.SUBJECT_VARS[sub]
#
#         student_answer = ei.get_obj_student_answer(request=request)
#         answer_string, is_confirmed = ei.get_tuple_answer_string_confirm(request=request, sub=sub)
#         if is_confirmed:
#             setattr(student_answer, field, answer_string)
#             setattr(student_answer, f'{field}_confirmed', is_confirmed)
#             student_answer.save()
#
#         next_url = ei.get_str_next_url(student_answer=student_answer)
#
#         context = update_context_data(
#             header=f'{subject} 답안 제출',
#             is_confirmed=is_confirmed,
#             next_url=next_url,
#         )
#         return render(request, 'a_score/snippets/modal_answer_confirmed.html', context)
#     else:
#         return redirect('predict:answer-input', sub)
