from bs4 import BeautifulSoup as bs

from psat import forms as psat_forms
from psat.models import psat_data_models
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Comment views."""
    model = psat_data_models.Comment
    form_class = psat_forms.CommentForm

    def get_comment_title(self):
        comment = self.request.POST.get('comment')
        if comment:
            soup = bs(comment, 'html.parser')
            text_comment = soup.get_text()
            comment_title = text_comment[:20]
            return comment_title

    def get_additional_data_for_create(self, form):
        problem_id = self.kwargs.get('problem_id')
        form.user = self.request.user
        form.problem_id = problem_id
        form.title = self.get_comment_title()
        return form

    @staticmethod
    def get_sub_title_from_comment(comment):
        return f'{comment.year}년 {comment.exam} {comment.subject} {comment.number}번'

    def get_replies_from_comment(self, comment):
        return self.comment_model.objects.filter(parent=comment)
