from psat import forms as psat_forms
from psat.models import psat_data_models
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Memo views."""
    model = psat_data_models.Memo
    form_class = psat_forms.MemoForm
    context_object_name = 'my_memo'

    def get_my_memo_by_problem(self, problem):
        return self.memo_model.objects.filter(
            problem=problem, user_id=self.request.user.id).first()
