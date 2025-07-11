import django_filters

from . import models
from .models import choices

CHOICES_LIKE = (
    ('all', '즐겨찾기 지정'),
    ('true', '즐겨찾기 추가'),
    ('false', '즐겨찾기 제거'),
    ('none', '즐겨찾기 미지정'),
)
CHOICES_RATE = (
    ('all', '난이도 지정'),
    ('5', '★★★★★'),
    ('4', '★★★★☆'),
    ('3', '★★★☆☆'),
    ('2', '★★☆☆☆'),
    ('1', '★☆☆☆☆'),
    ('none', '난이도 미지정'),
)
CHOICES_SOLVE = (
    ('all', '정답 확인'),
    ('true', '맞힌 문제'),
    ('false', '틀린 문제'),
    ('none', '정답 미확인'),
)
CHOICES_MEMO = (
    ('all', '메모 작성'),
    ('none', '메모 미작성'),
)
CHOICES_TAG = (
    ('all', '태그 작성'),
    ('none', '태그 미작성'),
)
CHOICES_COMMENT = (
    ('all', '코멘트 작성'),
    ('none', '코멘트 미작성'),
)


class LeetFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(
        field_name='year',
        label='',
        empty_label='[전체 연도]',
        choices=choices.year_choice,
    )
    is_active = django_filters.ChoiceFilter(
        field_name='is_active',
        label='',
        empty_label='[활성 상태]',
        choices={'True': '활성', 'False': '비활성'},
    )

    class Meta:
        model = models.Leet
        fields = ['year']

    @property
    def qs(self):
        return super().qs.prefetch_related('problems').order_by('-id')


class AnonymousProblemFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(
        field_name='leet__year',
        label='',
        empty_label='[전체 연도]',
        choices=choices.year_choice,
    )
    subject = django_filters.ChoiceFilter(
        field_name='subject',
        label='',
        empty_label='[전체 과목]',
        choices=choices.subject_choice,
    )

    class Meta:
        model = models.Problem
        fields = ['year', 'subject']

    @property
    def qs(self):
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        queryset = super().qs.select_related('leet').prefetch_related(
            'like_users', 'rate_users', 'solve_users', 'memo_users', 'comment_users',
            'likes', 'rates', 'solves', 'memos', 'comments',
        ).filter(leet__is_active=True)
        if keyword:
            return queryset.filter(data__icontains=keyword)
        return queryset


class ProblemFilter(AnonymousProblemFilter):
    likes = django_filters.ChoiceFilter(
        label='',
        empty_label='[즐겨찾기]',
        choices=CHOICES_LIKE,
        method='filter_likes',
    )
    rates = django_filters.ChoiceFilter(
        label='',
        empty_label='[난이도]',
        choices=CHOICES_RATE,
        method='filter_rates',
    )
    solves = django_filters.ChoiceFilter(
        label='',
        empty_label='[정답]',
        choices=CHOICES_SOLVE,
        method='filter_solves',
    )
    memos = django_filters.ChoiceFilter(
        label='',
        empty_label='[메모]',
        choices=CHOICES_MEMO,
        method='filter_memos',
    )
    tags = django_filters.ChoiceFilter(
        label='',
        empty_label='[태그]',
        choices=CHOICES_TAG,
        method='filter_tags',
    )
    # comments = django_filters.ChoiceFilter(
    #     label='',
    #     empty_label='[코멘트]',
    #     choices=CHOICES_COMMENT,
    #     method='filter_comments',
    # )

    class Meta:
        model = models.Problem
        fields = ['year', 'subject', 'likes', 'rates', 'solves', 'memos', 'tags']

    def get_lookup_dict(self, filter_name: str):
        return {f'{filter_name}_users': self.request.user, f'{filter_name}s__is_active': True}

    @staticmethod
    def get_filter_dict(queryset, lookup_dict):
        return {'all': queryset.filter(**lookup_dict), 'none': queryset.exclude(**lookup_dict)}

    def filter_likes(self, queryset, _, value):
        lookup_dict = self.get_lookup_dict('like')
        filter_dict = self.get_filter_dict(queryset, lookup_dict)
        filter_dict.update({
            'true': queryset.filter(likes__is_liked=True, **lookup_dict),
            'false': queryset.filter(likes__is_liked=False, **lookup_dict),
        })
        return filter_dict[value]

    def filter_rates(self, queryset, _, value):
        lookup_dict = self.get_lookup_dict('rate')
        filter_dict = self.get_filter_dict(queryset, lookup_dict)
        filter_dict.update({
            '1': queryset.filter(rates__rating=1, **lookup_dict),
            '2': queryset.filter(rates__rating=2, **lookup_dict),
            '3': queryset.filter(rates__rating=3, **lookup_dict),
            '4': queryset.filter(rates__rating=4, **lookup_dict),
            '5': queryset.filter(rates__rating=5, **lookup_dict),
        })
        return filter_dict[value]

    def filter_solves(self, queryset, _, value):
        lookup_dict = self.get_lookup_dict('solve')
        filter_dict = self.get_filter_dict(queryset, lookup_dict)
        filter_dict.update({
            'true': queryset.filter(solves__is_correct=True, **lookup_dict),
            'false': queryset.filter(solves__is_correct=False, **lookup_dict),
        })
        return filter_dict[value]

    def filter_memos(self, queryset, _, value):
        lookup_dict = self.get_lookup_dict('memo')
        filter_dict = self.get_filter_dict(queryset, lookup_dict)
        return filter_dict[value]

    def filter_tags(self, queryset, _, value):
        lookup_dict = self.get_lookup_dict('tag')
        filter_dict = self.get_filter_dict(queryset, lookup_dict)
        return filter_dict[value]

    # def filter_comments(self, queryset, _, value):
    #     filter_dict = {
    #         'all': queryset.filter(comment_users__isnull=False),
    #         'none': queryset.exclude(comment_users__isnull=True),
    #     }
    #     return filter_dict[value]


class ProblemTagFilter(django_filters.FilterSet):
    is_tagged = django_filters.ChoiceFilter(
        label='',
        empty_label='[전체 문제]',
        choices=(
            (True, '[태그된 문제]'),
        ),
        method='filter_tagged_problems'
    )

    class Meta:
        model = models.Problem
        fields = ['is_tagged']

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            if 'is_tagged' not in data:
                data['is_tagged'] = True
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        return super().qs.select_related('leet').distinct()

    @staticmethod
    def filter_tagged_problems(queryset, _, value):
        queryset = queryset.select_related('leet').distinct()
        if value:
            return queryset.filter(tagged_problems__isnull=False, tagged_problems__is_active=True)
        return queryset


class ProblemTaggedItemFilter(django_filters.FilterSet):
    is_active = django_filters.ChoiceFilter(
        field_name='is_active',
        label='',
        empty_label='[전체 태그]',
        choices=(
            (True, '[활성화된 태그]'),
            (False, '[비활성된 태그]'),
        ),
    )

    class Meta:
        model = models.ProblemTaggedItem
        fields = ['is_active']

    def __init__(self, data=None, *args, **kwargs):
        if data is not None:
            data = data.copy()
            if 'is_active' not in data:
                data['is_active'] = True
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        return super().qs.select_related('tag', 'content_object', 'content_object__leet', 'user')
