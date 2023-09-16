import django_filters

from .models import Problem


class PsatProblemFilter(django_filters.FilterSet):
    class Meta:
        model = Problem
        fields = ['exam__year', 'exam__ex', 'exam__sub']
