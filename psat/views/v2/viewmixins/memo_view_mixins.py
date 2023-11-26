from common.constants.icon_set import ConstantIconSet
from psat.forms import MemoForm
from psat.models import Memo
from reference.models.psat_models import PsatProblem


class MemoViewMixIn(
    ConstantIconSet,
):
    """Setting mixin for Memo views."""
    kwargs: dict
    object: any

    model = Memo
    lookup_field = 'id'
    lookup_url_kwarg = 'memo_id'
    form_class = MemoForm
    context_object_name = 'my_memo'
    template_name = 'psat/v2/snippets/memo_container.html'

    @property
    def problem_id(self) -> int | None:
        """Get problem_id in case of memo_create."""
        problem_id = self.kwargs.get('problem_id')
        return int(problem_id) if problem_id else None

    @property
    def problem(self):
        """Return problem in the Problem model if problem_id exists."""
        if self.problem_id:
            return PsatProblem.objects.get(id=self.problem_id)
