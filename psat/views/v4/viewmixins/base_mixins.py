from django.db.models import F, Q
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from reference.models import psat_models as reference_models


class BaseMixin(ConstantIconSet):
    menu = 'psat'

    request: any
    kwargs: dict

    user_id: int | None
    view_type: str
    info: dict

    problem_id: str
    problem: reference_models.PsatProblem.objects

    year: str
    ex: str
    sub: str
    psat: reference_models.Psat.objects

    sub_title: str

    page_number: str
    likes: str
    rates: str
    solves: str
    memos: str
    tags: str
    keyword: str

    ip_address: str
    base_url: str
    url_options: str
    pagination_url: str

    custom_data: dict[str, reference_models.PsatProblem.objects]

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None
        self.view_type = self.kwargs.get('view_type', 'problem')
        self.info = self.get_info()

        self.problem_id = self.kwargs.get('problem_id') or self.request.GET.get('problem_id')
        self.problem = reference_models.PsatProblem.objects.none()
        if self.problem_id:
            self.problem = self.get_problem()

        self.year = self.request.GET.get('year', '')
        self.ex = self.request.GET.get('ex', '')
        self.sub = self.request.GET.get('sub', '')
        self.psat = self.get_psat()

        self.sub_title = self.get_sub_title()

        self.page_number = self.request.GET.get('page', '1')
        self.likes = self.request.GET.get('likes', '')
        self.rates = self.request.GET.get('rates', '')
        self.solves = self.request.GET.get('solves', '')
        self.memos = self.request.GET.get('memos', '')
        self.tags = self.request.GET.get('tags', '')
        self.keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')

        self.ip_address = self.request.META.get('REMOTE_ADDR')
        self.base_url = reverse_lazy('psat:base')
        self.url_options = (
            f'?year={self.year}&ex={self.ex}&sub={self.sub}&page={self.page_number}'
            f'&likes={self.likes}&rates={self.rates}&solves={self.solves}'
            f'&memos={self.memos}&tags={self.tags}&keyword={self.keyword}'
        )
        self.pagination_url = f'{self.base_url}{self.url_options}'

        self.custom_data = self.get_custom_data()

    def get_psat(self) -> reference_models.Psat.objects:
        psat_filter = Q()
        if self.year:
            psat_filter &= Q(year=self.year)
        if self.ex:
            psat_filter &= Q(exam__abbr=self.ex)
        if self.sub:
            psat_filter &= Q(subject__abbr=self.sub)
        return reference_models.Psat.objects.filter(psat_filter).select_related('exam', 'subject').first()

    def get_sub_title(self) -> str:
        title_parts = []
        if self.year:  # year
            title_parts.append(f'{self.psat.year}년')
        if self.ex:  # ex
            title_parts.append(self.psat.exam.name)
        if self.sub:  # sub
            title_parts.append(self.psat.subject.name)
        if not self.year and not self.ex and not self.sub:  # all
            title_parts.append('전체')
        sub_title = f'{" ".join(title_parts)} 기출문제'
        return sub_title

    def get_info(self) -> dict[str, str]:
        """ Get the meta-info for the current view. """
        color_dict = {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
            'memo': 'warning',
            'tag': 'primary',
        }
        return {
            'menu': 'psat',
            'view_type': self.view_type,
            'color': color_dict[self.view_type],
        }

    def get_problem(self) -> reference_models.PsatProblem.objects:
        return (
            reference_models.PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .get(id=self.problem_id)
        )

    def get_custom_data(self) -> dict[str, reference_models.PsatProblem.objects]:
        """ Get all kinds of custom data. """
        problem_id = self.kwargs.get('problem_id')

        values_list_keys = ['id', 'psat_id', 'year', 'exam', 'subject', 'number']
        queryset = (
            reference_models.PsatProblem.objects
            .only('id', 'psat_id', 'number', 'answer', 'question')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .order_by('-psat__year', 'id')
        )

        if problem_id:
            problem = reference_models.PsatProblem.objects.get(id=problem_id)
            problem_data = queryset.filter(psat=problem.psat).values(*values_list_keys)
        else:
            problem_data = {}

        if self.user_id:
            queryset = queryset.prefetch_related('likes', 'rates', 'solves')
            like_data = (
                queryset.filter(likes__is_liked=True, likes__user_id=self.user_id)
                .annotate(is_liked=F('likes__is_liked'))
                .values(*values_list_keys, 'is_liked'))
            rate_data = (
                queryset.filter(rates__isnull=False, rates__user_id=self.user_id)
                .annotate(rating=F('rates__rating'))
                .values(*values_list_keys, 'rating'))
            solve_data = (
                queryset.filter(solves__isnull=False, solves__user_id=self.user_id)
                .annotate(user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
                .values(*values_list_keys, 'user_answer', 'is_correct'))
            memo_data = (
                queryset.filter(memos__isnull=False, memos__user_id=self.user_id)
                .values(*values_list_keys))
            tag_data = (
                queryset.filter(tags__isnull=False, tags__user_id=self.user_id)
                .values(*values_list_keys))
            comment_data = (
                queryset.filter(comments__isnull=False, comments__user_id=self.user_id)
                .values(*values_list_keys))
        else:
            like_data = rate_data = solve_data = memo_data = tag_data = comment_data = queryset.none()

        return {
            'problem': problem_data,
            'search': problem_data,
            'like': like_data,
            'rate': rate_data,
            'solve': solve_data,
            'memo': memo_data,
            'tag': tag_data,
            'comment': comment_data,
        }
