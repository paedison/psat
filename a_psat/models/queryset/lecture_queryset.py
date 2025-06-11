from django.db import models


class LectureTagQuerySet(models.QuerySet):
    def my_tags(self, user, lecture):
        return self.filter(
            tagged_items__user=user,
            tagged_items__content_object=lecture,
            tagged_items__active=True,
        ).values_list('name', flat=True)


class LectureTaggedItemQuerySet(models.QuerySet):
    def my_tag(self, user):
        return self.filter(user=user, active=True).select_related('user', 'content_object')


class LectureQuerySet(models.QuerySet):
    def order_by_subject_code(self):
        return self.annotate(
            subject_code=models.Case(
                models.When(subject='공부', then=0),
                models.When(subject='언어', then=1),
                models.When(subject='자료', then=2),
                models.When(subject='상황', then=3),
                default=4,
                output_field=models.IntegerField(),
            )
        ).order_by('subject_code')


class LectureOpenQuerySet(models.QuerySet):
    pass


class LectureLikeQuerySet(models.QuerySet):
    pass


class LectureMemoQuerySet(models.QuerySet):
    def my_memo(self, user, lecture):
        return self.filter(user=user, lecture=lecture).select_related('user', 'lecture').first()


class LectureCommentQuerySet(models.QuerySet):
    pass
