from common.constants.icon_set import ConstantIconSet
from psat import forms as custom_forms
from psat import models as custom_models
from reference.models import psat_models as reference_models


class BaseMixIn(ConstantIconSet):
    """Setting mixin for Memo views."""
    request: any
    kwargs: dict
    object: any

    model = custom_models.Comment
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'
    form_class = custom_forms.CommentForm
    context_object_name = 'comments'
    template_name = 'psat/v4/snippets/comment_container.html'

    problem_id: int
    comment_id: str
    problem: reference_models.PsatProblem.objects
    comment: reference_models.PsatProblem.objects

    parent_id: str

    def get_properties(self):
        self.comment_id = self.kwargs.get('comment_id')
        self.problem_id = self.kwargs.get('problem_id')
        self.comment = custom_models.Comment.objects.none()
        self.problem = reference_models.PsatProblem.objects.none()

        if self.problem_id:
            self.problem = reference_models.PsatProblem.objects.get(id=self.problem_id)
        elif self.comment_id:
            self.comment = custom_models.Comment.objects.get(id=self.comment_id)

        self.parent_id = self.request.GET.get('parent_id')
