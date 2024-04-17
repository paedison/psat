from django.db.models import F, Q

from common.constants.icon_set import ConstantIconSet
from reference.models import psat_models as reference_models


class BaseMixin(ConstantIconSet):
    menu = 'psat'

    request: any
    kwargs: dict

    def get_user_id(self):
        return self.request.user.id if self.request.user.is_authenticated else None

    def get_view_type(self):
        return self.kwargs.get('view_type', 'problem')

    def get_year_ex_sub(self):
        year = self.request.GET.get('year', '')
        ex = self.request.GET.get('ex', '')
        sub = self.request.GET.get('sub', '')
        return year, ex, sub

    def get_problem_id(self):
        return self.kwargs.get('problem_id') or self.request.GET.get('problem_id')

    def get_page_number(self):
        return self.request.GET.get('page', '1')

    def get_keyword(self):
        return self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')

    def get_ip_address(self):
        return self.request.META.get('REMOTE_ADDR')

    def get_url_options(self):
        year = self.request.GET.get('year', '')
        ex = self.request.GET.get('ex', '')
        sub = self.request.GET.get('sub', '')
        page_number = self.request.GET.get('page', '1')
        likes = self.request.GET.get('likes', '')
        rates = self.request.GET.get('rates', '')
        solves = self.request.GET.get('solves', '')
        memos = self.request.GET.get('memos', '')
        tags = self.request.GET.get('tags', '')
        keyword = self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')
        return (
            f'year={year}&ex={ex}&sub={sub}&page={page_number}'
            f'&likes={likes}&rates={rates}&solves={solves}'
            f'&memos={memos}&tags={tags}&keyword={keyword}'
        )

    @staticmethod
    def get_psat_from_year_ex_sub(year=None, ex=None, sub=None) -> reference_models.Psat.objects:
        psat_filter = Q()
        if year:
            psat_filter &= Q(year=year)
        if ex:
            psat_filter &= Q(exam__abbr=ex)
        if sub:
            psat_filter &= Q(subject__abbr=sub)
        return reference_models.Psat.objects.filter(psat_filter).select_related('exam', 'subject').first()

    @staticmethod
    def get_sub_title_from_psat(psat=None, year=None, ex=None, sub=None, end_string='기출문제') -> str:
        title_parts = []
        if psat:
            if year:  # year
                title_parts.append(f'{psat.year}년')
            if ex:  # ex
                title_parts.append(psat.exam.name)
            if sub:  # sub
                title_parts.append(psat.subject.name)
            if not year and not ex and not sub:  # all
                title_parts.append('전체')
        else:
            title_parts.append('전체')
        sub_title = f'{" ".join(title_parts)} {end_string}'
        return sub_title

    @staticmethod
    def get_info(view_type) -> dict[str, str]:
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
            'view_type': view_type,
            'color': color_dict[view_type],
        }

    @staticmethod
    def get_problem_from_problem_id(problem_id) -> reference_models.PsatProblem.objects:
        return (
            reference_models.PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .get(id=problem_id)
        )

    def get_custom_data(self) -> dict[str, reference_models.PsatProblem.objects]:
        """ Get all kinds of custom data. """
        problem_id = self.kwargs.get('problem_id')
        user_id = self.get_user_id()

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

        if user_id:
            queryset = queryset.prefetch_related('likes', 'rates', 'solves')
            like_data = (
                queryset.filter(likes__is_liked=True, likes__user_id=user_id)
                .annotate(is_liked=F('likes__is_liked'))
                .values(*values_list_keys, 'is_liked'))
            rate_data = (
                queryset.filter(rates__isnull=False, rates__user_id=user_id)
                .annotate(rating=F('rates__rating'))
                .values(*values_list_keys, 'rating'))
            solve_data = (
                queryset.filter(solves__isnull=False, solves__user_id=user_id)
                .annotate(user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
                .values(*values_list_keys, 'user_answer', 'is_correct'))
            memo_data = (
                queryset.filter(memos__isnull=False, memos__user_id=user_id)
                .values(*values_list_keys))
            tag_data = (
                queryset.filter(tags__isnull=False, tags__user_id=user_id)
                .values(*values_list_keys))
            collection_data = (
                queryset.filter(
                    collection_items__isnull=False,
                    collection_items__collection__user_id=user_id,
                    collection_items__is_active=True,
                )
                .values(*values_list_keys))
            comment_data = (
                queryset.filter(comments__isnull=False, comments__user_id=user_id)
                .values(*values_list_keys))
        else:
            like_data = rate_data = solve_data = memo_data = tag_data = collection_data = comment_data = queryset.none()

        return {
            'problem': problem_data,
            'search': problem_data,
            'like': like_data,
            'rate': rate_data,
            'solve': solve_data,
            'memo': memo_data,
            'tag': tag_data,
            'collection': collection_data,
            'comment': comment_data,
        }
