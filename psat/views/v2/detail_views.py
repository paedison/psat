from vanilla import TemplateView

from reference.models import PsatProblem
from .viewmixins import PsatDetailViewMixIn, PsatCustomInfo, PsatIconSet


class BaseDetailView(
    PsatCustomInfo,
    PsatDetailViewMixIn,
    TemplateView,
):
    """Represent PSAT base detail view."""

    def get_template_names(self) -> str:
        base_template = 'psat/v2/problem_detail.html'
        main_template = f'{base_template}#detail_main'

        icon_container = 'psat/v2/snippets/icon_container.html'
        icon_template = f'{icon_container}#{self.view_type}'

        if self.request.method == 'GET':
            return main_template if self.request.htmx else base_template
        else:
            return icon_template

    def post(self, request, *args, **kwargs):
        option_dict = {
            'like': 'is_liked',
            'rate': 'rating',
            'solve': 'is_correct'
        }
        option_name = option_dict[self.view_type]
        context = {
            option_name: getattr(self.data_instance, option_name),
            # Icons
            'icon_like': self.icon_like,
            'icon_rate': self.icon_rate,
            'icon_solve': self.icon_solve,
        }
        return self.render_to_response(context)

    def get_context_data(self, **kwargs) -> dict:
        return {
            # List view info & title
            'info': self.info,
            'title': self.title,

            # Detail view template variables
            'num_range': self.num_range,
            'anchor_id': self.problem_id - int(self.object.number),

            # Icons
            'icon_like': self.icon_like,
            'icon_rate': self.icon_rate,
            'icon_solve': self.icon_solve,
            'icon_nav': self.icon_nav,

            # Page objectives & range
            'problem': self.get_custom_info(self.object),
            'prev_prob': self.prev_prob,
            'next_prob': self.next_prob,
            'list_data': self.list_data,
            'memo': self.memo,
            'my_tag': self.my_tag,
        }


class RateModalView(TemplateView):
    template_name = 'psat/v2/snippets/icon_container.html#rate_modal'

    def get_context_data(self, **kwargs):
        return {
            'problem_id': self.request.GET.get('problem_id'),
            'icon_id': self.request.GET.get('icon_id'),
        }


class SolveModalView(PsatIconSet, TemplateView):
    template_name = 'psat/v2/snippets/answer_container.html#answer_modal'

    @property
    def problem_id(self) -> int:
        return int(self.request.POST.get('problem_id'))

    @property
    def answer(self) -> int | None:
        answer = self.request.POST.get('answer')
        return int(answer) if answer else None

    @property
    def is_correct(self) -> bool | None:
        problem = PsatProblem.objects.get(id=self.problem_id)
        return None if self.answer is None else (self.answer == problem.answer)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            'problem_id': self.problem_id,
            'answer': self.answer,
            'is_correct': self.is_correct,
            'icon_solve': self.icon_solve,
        }


base_view = BaseDetailView.as_view()
rate_modal_view = RateModalView.as_view()
solve_modal_view = SolveModalView.as_view()
