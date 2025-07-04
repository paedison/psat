from django.apps import apps
from django.db import models


class LeetQuerySet(models.QuerySet):
    def predict_leet_active(self):
        return self.filter(predict_leet__is_active=True).select_related('predict_leet').order_by('-id')


class ProblemTagQuerySet(models.QuerySet):
    def user_tags_for_problem(self, user, problem):
        return self.filter(
            tagged_items__user=user,
            tagged_items__content_object=problem,
            tagged_items__is_active=True,
        ).values_list('name', flat=True)


class ProblemQuerySet(models.QuerySet):
    def base_list(self, problem):
        return self.filter(leet=problem.leet, subject=problem.subject)

    def like_list(self, problem, user):
        return (
            self.base_list(problem).prefetch_related('likes')
            .filter(likes__is_liked=True, likes__user=user, likes__is_active=True)
            .annotate(is_liked=models.F('likes__is_liked'))
        )

    def rate_list(self, problem, user):
        return (
            self.base_list(problem).prefetch_related('rates')
            .filter(rates__isnull=False, rates__user_id=user, rates__is_active=True)
            .annotate(rating=models.F('rates__rating'))
        )

    def solve_list(self, problem, user):
        return (
            self.base_list(problem).prefetch_related('solves')
            .filter(solves__isnull=False, solves__user_id=user, solves__is_active=True)
            .annotate(user_answer=models.F('solves__answer'), is_correct=models.F('solves__is_correct'))
        )

    def memo_list(self, problem, user):
        return (
            self.base_list(problem).prefetch_related('memos')
            .filter(memos__isnull=False, memos__user_id=user, memos__is_active=True)
        )

    def tag_list(self, problem, user):
        return (
            self.base_list(problem).prefetch_related('tagged_problems')
            .filter(tags__isnull=False, tagged_problems__user_id=user).distinct()
        )

    def filtered_problem_by_leet(self, leet):
        return (
            self.select_related('leet').filter(leet=leet)
            .annotate(no=models.F('number'), ans=models.F('answer'), ans_official=models.F('answer'))
            .order_by('subject', 'no')
        )

    def annotate_subject_code(self):
        return self.annotate(
            subject_code=models.Case(
                models.When(subject='언어', then=1),
                models.When(subject='자료', then=2),
                models.When(subject='상황', then=3),
                default=4,
                output_field=models.IntegerField(),
            )
        )


class ProblemOpenQuerySet(models.QuerySet):
    pass


class ProblemLikeQuerySet(models.QuerySet):
    pass


class ProblemRateQuerySet(models.QuerySet):
    pass


class ProblemSolveQuerySet(models.QuerySet):
    pass


class ProblemMemoQuerySet(models.QuerySet):
    def user_memo_for_problem(self, user, problem):
        return self.filter(user=user, problem=problem).first()


class ProblemCollectionQuerySet(models.QuerySet):
    def user_collection(self, user):
        return self.filter(user=user, is_active=True).order_by('order')

    def user_collection_for_modal(self, user, pk):
        item_model = apps.get_model('a_leet', 'ProblemCollectionItem')
        collection_ids = (
            item_model.objects.filter(collection__user=user, problem_id=pk, is_active=True)
            .values_list('collection_id', flat=True).distinct()
        )
        item_exists = models.Case(
            models.When(id__in=collection_ids, then=1),
            output_field=models.BooleanField(),
            default=0,
        )
        return self.user_collection(user).annotate(item_exists=item_exists)


class ProblemCollectionItemQuerySet(models.QuerySet):
    def collection_item(self, collection):
        return self.filter(collection=collection, is_active=True).order_by('order')


class ProblemAnnotationQuerySet(models.QuerySet):
    pass


class ProblemCommentQuerySet(models.QuerySet):
    pass


class ProblemCommentLikeQuerySet(models.QuerySet):
    pass
