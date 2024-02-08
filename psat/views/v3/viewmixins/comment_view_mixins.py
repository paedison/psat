from common.constants.icon_set import ConstantIconSet
from psat import forms as custom_forms
from psat import models as custom_models
from reference.models import psat_models as reference_models


class BaseMixIn(ConstantIconSet):
    """Setting mixin for Memo views."""
    kwargs: dict
    object: any

    model = custom_models.Comment
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'
    form_class = custom_forms.CommentForm
    context_object_name = 'comments'
    template_name = 'psat/v3/snippets/comment_container.html'

    problem_id: str
    problem: reference_models.PsatProblem.objects

    def get_properties(self):
        self.problem_id = self.kwargs.get('problem_id')

        self.problem = None
        if self.problem_id:
            self.problem = reference_models.PsatProblem.objects.get(id=self.problem_id)


class CommentListViewMixin(ConstantIconSet):
    kwargs: dict
    object: any

    model = custom_models.Comment
