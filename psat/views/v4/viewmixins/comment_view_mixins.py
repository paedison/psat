from bs4 import BeautifulSoup as bs
from django.db.models import F

from psat import forms, models
from . import base_mixins


class BaseMixIn(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    """Setting mixin for Comment views."""
    model = models.Comment
    form_class = forms.CommentForm

    def get_comment_qs(self):
        return (
            self.comment_model.objects
            .select_related(
                'user', 'problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
            .annotate(
                username=F('user__username'),
                year=F('problem__psat__year'), number=F('problem__number'),
                ex=F('problem__psat__exam__abbr'), exam=F('problem__psat__exam__name'),
                sub=F('problem__psat__subject__abbr'), subject=F('problem__psat__subject__name')))

    def get_single_comment(self, comment_id):
        if comment_id:
            return self.get_comment_qs().get(id=comment_id)

    def get_all_comments(self, problem_id=None):
        qs = self.get_comment_qs()
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        parent_comments = qs.filter(parent__isnull=True).order_by('-timestamp')
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
        all_comments = []
        for comment in parent_comments:
            all_comments.append(comment)
            all_comments.extend(child_comments.filter(parent=comment))
        return all_comments

    def get_all_comments_of_parent_comment(self, parent_comment):
        qs = self.get_comment_qs().filter(parent=parent_comment)
        child_comments = qs.exclude(parent__isnull=True).order_by('parent_id', '-timestamp')
        all_comments = [parent_comment]
        for comment in child_comments:
            all_comments.append(comment)
        return all_comments

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
