import django.contrib.auth.mixins as auth_mixins
import vanilla
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import base_mixins, normal_view_mixins


class IndexView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.IndexViewMixIn,
    vanilla.TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/predict_v1/predict_index.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#index_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'answer_uploaded': self.answer_uploaded,
            'category': self.category,
            'year': self.year,
            'ex': self.ex,
            'exam': self.exam_name,
            'round': self.round,
            'units': self.units,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,

            # student_info
            'student': self.student,
            'departments': self.departments,

            # answer_student
            'answer_student_count': self.answer_student_count,
            'answer_student_data': self.answer_student_data,

            # score_sheet
            'student_score': self.student_score,
            'all_score_stat': self.all_score_stat,

            # 'rates_eoneo': self.all_answer_rates['언어'],
            # 'rates_jaryo': self.all_answer_rates['자료'],
            # 'rates_sanghwang': self.all_answer_rates['상황'],
            # 'rates_heonbeob': self.all_answer_rates['헌법'],
        }


class StudentCreateView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.IndexViewMixIn,
    vanilla.FormView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    template_name = 'score/predict_v1/predict_index.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#index_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get_form_class(self):
        return self.student_form

    def get(self, request, *args, **kwargs):
        self.get_properties()
        if self.student:
            return HttpResponseRedirect(reverse_lazy('predict:index'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_properties()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form = form.save(commit=False)
        with transaction.atomic():
            form.user_id = self.request.user.id
            form.category = self.category
            form.year = self.year
            form.ex = self.ex
            form.round = self.round
            form.save()
        return HttpResponseRedirect(reverse_lazy('predict:index'))

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # base info
                'info': self.info,
                'category': self.category,
                'year': self.year,
                'ex': self.ex,
                'exam': self.exam_name,
                'round': self.round,
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
    template_name = 'score/predict_v1/snippets/predict_student_info.html#student_create_department'

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
    template_name = 'score/predict_v1/predict_answer_input.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def get(self, request, *args, **kwargs):
        self.get_properties()
        if not self.student:
            return HttpResponseRedirect(reverse_lazy('predict:student_create'))
        if self.is_confirmed:
            return HttpResponseRedirect(reverse_lazy('predict:index'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                # base info
                'info': self.info,
                'category': self.category,
                'year': self.year,
                'ex': self.ex,
                'exam': self.exam_name,
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
    template_name = 'score/predict_v1/predict_answer_input.html#scored_form'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        number = self.request.POST.get('number')
        answer = self.request.POST.get('answer')
        student_id = self.request.POST.get('student_id')

        scored, _ = self.answer_model.objects.get_or_create(student_id=student_id, sub=self.sub)
        setattr(scored, f'prob{number}', answer)
        scored.save()
        scored_problem = {
            'problem': {'number': number, 'answer_student': int(answer)},
            'answer': int(answer),
        }

        return {
            'sub': self.sub,
            'scored': scored_problem,
        }


class AnswerConfirmView(
    auth_mixins.LoginRequiredMixin,
    normal_view_mixins.AnswerConfirmViewMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for confirming answers. """
    menu = 'score'
    template_name = 'score/predict_v1/snippets/predict_modal.html#score_confirmed'

    def get(self, request, *args, **kwargs):
        self.get_properties()
        return HttpResponseRedirect(reverse_lazy('predict:answer_input', args=[self.sub]))

    def post(self, request, *args, **kwargs):
        self.get_properties()
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        return {
            'header': f'{self.sub} 답안 제출',
            'is_confirmed': self.is_confirmed,
            'next_url': self.next_url,
        }


index_view = IndexView.as_view()

student_create_view = StudentCreateView.as_view()
student_create_department = StudentCreateDepartment.as_view()

answer_input_view = AnswerInputView.as_view()
answer_submit_view = AnswerSubmitView.as_view()
answer_confirm_view = AnswerConfirmView.as_view()
