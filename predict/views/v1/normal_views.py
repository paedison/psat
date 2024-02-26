import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import base_mixins, normal_view_mixins


class IndexView(
    normal_view_mixins.IndexViewMixIn,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/normal/predict_index.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#index_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # base info
                'info': self.info,
                'exam': self.exam,
                'current_time': self.current_time,
                'min_participants': self.min_participants,
                'title': 'Predict',
                'sub_title': self.sub_title,

                # icons
                'icon_menu': self.ICON_MENU['predict'],
                'icon_subject': self.ICON_SUBJECT,
                'icon_nav': self.ICON_NAV,

                # index_info_student: 수험 정보
                'units': self.units,
                'departments': self.departments,
                'student': self.student,
                'location': self.location,

                # index_info_answer: 답안 제출 현황
                'info_answer_student': self.info_answer_student,

                # index_sheet_answer: 답안 확인
                'data_answer_correct': self.data_answer['answer_correct'],
                'data_answer_predict': self.data_answer['answer_predict'],
                'data_answer_student': self.data_answer['answer_student'],

                # index_sheet_score: 성적 예측 I [전체 데이터]
                'score_student': self.score_student,
                'all_score_stat': self.all_score_stat,

                # index_sheet_score_filtered: 성적 예측 II [정답 공개 전 데이터]
                'filtered_score_student': self.filtered_score_student,
                'filtered_all_score_stat': self.filtered_all_score_stat,
            }
        )
        return context


class UpdateInfoAnswer(IndexView):
    template_name = 'predict/v1/normal/snippets/update_info_answer.html'

    def get_template_names(self):
        return self.template_name


class UpdateSheetAnswer(IndexView):
    template_name = 'predict/v1/normal/snippets/update_sheet_answer.html'

    def get_template_names(self):
        return self.template_name


class UpdateSheetScore(IndexView):
    template_name = 'predict/v1/normal/snippets/update_sheet_score.html'

    def get_template_names(self):
        return self.template_name


class StudentCreateView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.IndexViewMixIn,
    vanilla.FormView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'predict/v1/normal/predict_index.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#index_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_form_class(self):
        return self.student_form

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse_lazy('predict_test:index'))

    def post(self, request, *args, **kwargs):
        self.get_properties()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form = form.save(commit=False)
        with transaction.atomic():
            form.user_id = self.request.user.id
            exam = self.exam_model.objects.get(
                category=self.category, year=self.year, ex=self.ex, round=self.round,
            )
            form.exam = exam
            form.save()
        return HttpResponseRedirect(reverse_lazy('predict_test:answer_input', args=['헌법']))

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # base info
                'info': self.info,
                'category': self.exam.category,
                'year': self.exam.year,
                'ex': self.exam.ex,
                'exam': self.exam.exam,
                'round': self.round,
                'unit_id': self.request.POST.get('unit_id'),
                'units': self.units,
                'title': 'Score',
                'sub_title': self.sub_title,

                # icons
                'icon_menu': self.ICON_MENU['score'],
                'icon_subject': self.ICON_SUBJECT,
                'icon_nav': self.ICON_NAV,

                # student info
                'student': self.student,
                'departments': self.departments,
            }
        )
        return context


class StudentCreateDepartment(
    auth_mixins.LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Return department list for PSAT student create modal. """
    template_name = 'predict/v1/normal/snippets/index_info_student.html#student_create_department'

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        unit_id = self.request.POST.get('unit_id')
        departments = self.department_model.objects.filter(unit_id=unit_id)
        return {'departments': departments}


class AnswerInputView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.AnswerInputViewMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/normal/predict_answer_input.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        if not self.student:
            return HttpResponseRedirect(reverse_lazy('predict_test:student_create'))
        if self.is_confirmed:
            return HttpResponseRedirect(reverse_lazy('predict_test:index'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # base info
                'info': self.info,
                'category': self.exam.category,
                'year': self.exam.year,
                'ex': self.exam.ex,
                'exam': self.exam.exam,
                'sub': self.sub,
                'subject': self.subject,
                'title': 'Score',
                'sub_title': self.sub_title,

                # icons
                'icon_menu': self.ICON_MENU['score'],
                'icon_subject': self.ICON_SUBJECT,
                'icon_nav': self.ICON_NAV,

                'student': self.student,
                'answer_student': self.answer_student,
            }
        )
        return context


class AnswerSubmitView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.AnswerInputViewMixin,
    vanilla.TemplateView,
):
    menu = 'score'
    template_name = 'predict/v1/normal/predict_answer_input.html#scored_form'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        number = self.request.POST.get('number')
        answer = self.request.POST.get('answer')
        student_id = self.request.POST.get('student_id')
        id_prefix = self.request.POST.get('id_prefix')

        scored, _ = self.answer_model.objects.get_or_create(student_id=student_id, sub=self.sub)
        setattr(scored, f'prob{number}', answer)
        scored.save()
        scored_problem = {
            'problem': {'number': int(number), 'answer_student': int(answer)},
            'answer': int(answer),
        }
        context.update(
            {
                'sub': self.sub,
                'scored': scored_problem,
                'id_prefix': id_prefix,
            }
        )
        return context


class AnswerConfirmView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.AnswerConfirmViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for confirming answers. """
    menu = 'score'
    template_name = 'predict/v1/normal/snippets/predict_modal.html#score_confirmed'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return HttpResponseRedirect(reverse_lazy('predict_test:answer_input', args=[self.sub]))

    def post(self, request, *args, **kwargs):
        self.get_properties()
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return {
            'header': f'{self.subject} 답안 제출',
            'is_confirmed': self.is_confirmed,
            'next_url': self.next_url,
        }


index_view = IndexView.as_view()

student_create_view = StudentCreateView.as_view()
student_create_department = StudentCreateDepartment.as_view()

answer_input_view = AnswerInputView.as_view()
answer_submit_view = AnswerSubmitView.as_view()
answer_confirm_view = AnswerConfirmView.as_view()

update_info_answer = UpdateInfoAnswer.as_view()
update_sheet_answer = UpdateSheetAnswer.as_view()
update_sheet_score = UpdateSheetScore.as_view()
