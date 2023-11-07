from vanilla import TemplateView

from reference import models as reference_models
from score import models as score_models
from .viewmixins.list_viewmixins import ScoreCommonVariableSet, ScoreResultVariableSet, ScoreFilterVariableSet


class BaseView(
    ScoreCommonVariableSet,
    ScoreFilterVariableSet,
    ScoreResultVariableSet,
    TemplateView
):
    """ Represent information related TemporaryAnswer and ConfirmedAnswer models. """
    menu = 'score'
    template_name = 'score/v2/score_list.html'

    request: any

    def get_status(self):
        exam_count = reference_models.Psat.objects.filter(
            year=self.year,
            exam__abbr=self.ex,
        ).distinct().values_list('subject_id', flat=True).count()
        answer_exam_count = score_models.PsatConfirmedAnswer.objects.filter(
            user_id=self.user_id,
            problem__psat__year=self.year,
            problem__psat__exam__abbr=self.ex,
        ).distinct().values_list('problem__psat__subject_id', flat=True).count()
        return exam_count == answer_exam_count

    @property
    def queryset(self):
        return self.get_queryset()

    def get_queryset(self):
        queryset = reference_models.Psat.objects.filter(
            year=self.year, exam__abbr=self.ex,
        ).select_related('exam')

        for query in queryset:
            problems_count = query.psat_problems.count()
            submitted_answers_count = score_models.PsatConfirmedAnswer.objects.filter(
                user_id=self.user_id, problem__psat__exam_id=query.exam_id).count()
            if problems_count > 0:
                query.completed = problems_count == submitted_answers_count
        return queryset

    def get_template_names(self) -> str:
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > content(GET): content page
        :return: str
        """
        base_template = self.template_name
        main_template = f'{base_template}#list_main'
        if self.request.method == 'GET':
            return main_template if self.request.htmx else base_template
        else:
            return main_template

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        info = {
            'menu': self.menu,
            'view_type': self.menu,
            'type': f'{self.menu}List',
        }
        exam_name = self.get_exam_name()
        all_answer_set = self.get_all_answer_set()
        all_rank = self.get_all_rank()
        context = {
            'info': info,
            'year': self.year,
            'ex': self.ex,
            'exam': exam_name['exam'],
            'title': 'Score',
            'sub_title': exam_name['sub_title'],
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',

            'is_confirmed': self.get_status(),

            'student': all_rank['student'],
            'my_total_rank': all_rank['my_total_rank'],
            'my_department_rank': all_rank['my_department_rank'],

            'total_stat': self.get_stat('total'),
            'department_stat': self.get_stat('department'),

            'eoneo_answer': all_answer_set['eoneo_answer'],
            'jaryo_answer': all_answer_set['jaryo_answer'],
            'sanghwang_answer': all_answer_set['sanghwang_answer'],
            'heonbeob_answer': all_answer_set['heonbeob_answer'],

            'eoneo_temporary': all_answer_set['eoneo_temporary'],
            'jaryo_temporary': all_answer_set['jaryo_temporary'],
            'sanghwang_temporary': all_answer_set['sanghwang_temporary'],
            'heonbeob_temporary': all_answer_set['heonbeob_temporary'],

            'eoneo_rates': self.get_answer_rates('언어'),
            'jaryo_rates': self.get_answer_rates('자료'),
            'sanghwang_rates': self.get_answer_rates('상황'),
            'heonbeob_rates': self.get_answer_rates('헌법'),

            'page_obj': self.queryset,
            'year_option': self.year_option,
            'ex_option': self.ex_option,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_subject': self.ICON_SUBJECT,

        }
        return context


class ListFilterExamView(ScoreFilterVariableSet, TemplateView):
    template_name = 'score/v2/score_list.html#exam_select'

    def get_context_data(self, **kwargs) -> dict:
        year = self.request.POST.get('year')
        ex_list = (
            reference_models.Psat.objects.filter(year=year).distinct()
            .values_list('exam__abbr', 'exam__name').order_by('exam_id')
        )
        ex_option = self.get_option(ex_list)
        return {'ex_option': ex_option}

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


list_view = BaseView.as_view()
list_filter_exam_view = ListFilterExamView.as_view()