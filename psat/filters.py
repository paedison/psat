import django_filters

from .models import Problem


class PsatProblemFilter(django_filters.FilterSet):
    class Meta:
        model = Problem
        fields = ['exam__year', 'exam__ex', 'exam__sub']


class PsatLikeFilter(django_filters.FilterSet):
    class Meta:
        model = Problem
        fields = ['exam__sub', 'evaluation__is_liked']


class PsatRateFilter(django_filters.FilterSet):
    class Meta:
        model = Problem
        fields = ['exam__sub', 'evaluation__difficulty_rated']


class PsatAnswerFilter(django_filters.FilterSet):
    class Meta:
        model = Problem
        fields = ['exam__sub', 'evaluation__is_correct']
