import vanilla
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from .viewmixins import base_mixins, normal_view_mixins


class ListView(
    normal_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/score_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'title': 'Score',
            'sub_title': self.sub_title,
            'current_time': self.current_time,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,

            # page objectives
            'page_obj': self.page_obj,
            'page_range': self.page_range,
        }


class DetailView(
    LoginRequiredMixin,
    normal_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'score/prime_v3/score_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self) -> dict:
        self.get_properties()

        return {
            # base info
            'info': self.info,
            'year': self.year,
            'round': self.round,
            'title': 'Score',
            'sub_title': self.sub_title,

            # icons
            'icon_menu': self.ICON_MENU['score'],
            'icon_subject': self.ICON_SUBJECT,
            'icon_nav': self.ICON_NAV,

            # score_student.html
            'student': self.student,

            # score_sheet.html, score_chart.html
            'student_score': self.student_score,
            'stat_total': self.all_score_stat['전체'],
            'stat_department': self.all_score_stat['직렬'],

            # score_answers.html
            'answers_eoneo': self.all_answers['언어'],
            'answers_jaryo': self.all_answers['자료'],
            'answers_sanghwang': self.all_answers['상황'],
            'answers_heonbeob': self.all_answers['헌법'],

            'rates_eoneo': self.all_answer_rates['언어'],
            'rates_jaryo': self.all_answer_rates['자료'],
            'rates_sanghwang': self.all_answer_rates['상황'],
            'rates_heonbeob': self.all_answer_rates['헌법'],
        }


class PrintView(DetailView):
    template_name = 'score/prime_v3/score_print.html'
    view_type = 'print'


class NoOpenModalView(
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Represent modal view when there is no student data. """
    template_name = 'score/prime_v3/snippets/score_modal.html#no_open_modal'

    def get_context_data(self, **kwargs):
        self.get_properties()

        exam = {}
        for e in self.exam_list:
            if self.year == e['year'] and self.round == e['round']:
                exam = e
        return {'exam': exam}


class NoStudentModalView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Represent modal view when there is no student data. """
    template_name = 'score/prime_v3/snippets/score_modal.html#no_student_modal'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'year': self.year,
            'round': self.round,
        }


class StudentConnectModalView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.TemplateView,
):
    """ Represent modal view for connecting student data. """
    template_name = 'score/prime_v3/snippets/score_modal.html#student_connect'

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        prime = self.category_model.objects.filter(
            year=self.year, round=self.round).select_related('exam').first()
        exam = prime.exam.name
        return {
            'header': f'{self.year}년 대비 제{self.round}회 {exam} 수험 정보 입력',
            'year': self.year,
            'round': self.round,
        }


class StudentConnectView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.FormView,
):
    template_name = 'score/prime_v3/snippets/score_modal.html#student_info'

    def get_form_class(self):
        return self.student_form

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form(data=request.POST, files=request.FILES)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        self.get_properties()

        try:
            target_student = form.save(commit=False)
            target_student = self.student_model.objects.get(
                year=self.year,
                round=self.round,
                serial=target_student.serial,
                name=target_student.name,
                password=target_student.password,
            )
            verified_user, _ = self.verified_user_model.objects.get_or_create(
                user=self.request.user, student=target_student
            )
            context = self.get_context_data(
                form=form, year=self.year, round=self.round, user_verified=True)
            return self.render_to_response(context)

        except self.student_model.DoesNotExist:
            context = self.get_context_data(
                form=form, year=self.year, round=self.round, no_student=True)
            return self.render_to_response(context)

    def form_invalid(self, form):
        self.get_properties()

        context = self.get_context_data(form=form, year=self.year, round=self.round)
        return self.render_to_response(context)


class StudentResetView(
    LoginRequiredMixin,
    base_mixins.BaseMixin,
    vanilla.FormView,
):
    def post(self, request, *args, **kwargs):
        self.get_properties()

        try:
            verified_user = self.verified_user_model.objects.get(
                student__year=self.year, student__round=self.round, user_id=self.user_id)
            verified_user.delete()
        except self.verified_user_model.DoesNotExist:
            pass
        list_url = reverse_lazy('prime:list')
        return HttpResponseRedirect(list_url)


list_view = ListView.as_view()

detail_view = DetailView.as_view()
detail_print_view = PrintView.as_view()

no_open_modal_view = NoOpenModalView.as_view()
no_student_modal_view = NoStudentModalView.as_view()
student_connect_modal_view = StudentConnectModalView.as_view()

student_connect_view = StudentConnectView.as_view()
student_reset_view = StudentResetView.as_view()
