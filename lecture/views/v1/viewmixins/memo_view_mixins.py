from lecture import forms as lecture_forms
from lecture.models import custom_models
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Memo views."""
    model = custom_models.Memo
    form_class = lecture_forms.MemoForm
    context_object_name = 'my_memo'

    def get_my_memo_by_lecture(self, lecture):
        return self.memo_model.objects.filter(
            lecture=lecture, user_id=self.request.user.id).first()
