from bs4 import BeautifulSoup as bs

from lecture import forms as lecture_forms
from lecture.models import custom_models
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Comment views."""
    model = custom_models.Comment
    form_class = lecture_forms.CommentForm

    def get_comment_title(self):
        comment = self.request.POST.get('comment')
        if comment:
            soup = bs(comment, 'html.parser')
            text_comment = soup.get_text()
            comment_title = text_comment[:20]
            return comment_title

    def get_additional_data_for_create(self, form):
        lecture_id = self.kwargs.get('lecture_id')
        form.user = self.request.user
        form.lecture_id = lecture_id
        form.title = self.get_comment_title()
        return form

    @staticmethod
    def get_sub_title_from_comment(comment):
        return f'{comment.year}년 {comment.exam} {comment.subject} {comment.number}번'

    def get_replies_from_comment(self, comment):
        return self.comment_model.objects.filter(parent=comment)
