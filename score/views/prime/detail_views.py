from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from .viewmixins.detail_viewmixins import PrimeScoreDetailViewMixin


class BaseView(
    LoginRequiredMixin,
    TemplateView,
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    view_type = 'primeScore'
    template_name = 'score/prime/score_detail.html'
    request: any

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        variable = PrimeScoreDetailViewMixin(self.request, **self.kwargs)

        info = variable.get_info()
        all_answers = variable.get_all_answers()
        all_ranks = variable.get_all_ranks()
        all_stat = variable.get_all_stat()
        all_answer_rates = variable.get_all_answer_rates()

        return {
            'info': info,
            'year': variable.year,
            'round': variable.round,
            'title': variable.title,
            'sub_title': variable.sub_title,

            'eoneo_answer': all_answers['언어'],
            'jaryo_answer': all_answers['자료'],
            'sanghwang_answer': all_answers['상황'],
            'heonbeob_answer': all_answers['헌법'],

            'student': variable.student,
            'my_total_rank': all_ranks['전체'],
            'my_department_rank': all_ranks['직렬'],

            'total_stat': all_stat['전체'],
            'department_stat': all_stat['직렬'],

            'eoneo_rates': all_answer_rates['언어'],
            'jaryo_rates': all_answer_rates['자료'],
            'sanghwang_rates': all_answer_rates['상황'],
            'heonbeob_rates': all_answer_rates['헌법'],

            # Icons
            'icon_menu': variable.ICON_MENU['score'],
            'icon_subject': variable.ICON_SUBJECT,
            'icon_nav': variable.ICON_NAV,
        }


class PrintView(BaseView):
    template_name = 'score/prime/score_print.html'
    view_type = 'print'


base_view = BaseView.as_view()
print_view = PrintView.as_view()
