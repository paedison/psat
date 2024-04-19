from django.db import transaction
from django.db.models import F, Q

from psat.views.v4 import filters
from . import base_mixins


class BaseMixin(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    menu = 'psat'

    def get_view_type(self):
        return self.kwargs.get('view_type', 'problem')

    def get_year_ex_sub(self):
        year = self.request.GET.get('year', '')
        ex = self.request.GET.get('ex', '')
        sub = self.request.GET.get('sub', '')
        return year, ex, sub

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

    def get_psat_from_year_ex_sub(self, year=None, ex=None, sub=None):
        psat_filter = Q()
        if year:
            psat_filter &= Q(year=year)
        if ex:
            psat_filter &= Q(exam__abbr=ex)
        if sub:
            psat_filter &= Q(subject__abbr=sub)
        return self.psat_model.objects.filter(psat_filter).select_related('exam', 'subject').first()

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

    def get_custom_data(self) -> dict:
        """ Get all kinds of custom data. """
        problem_id = self.kwargs.get('problem_id')
        user_id = self.request.user.id

        values_list_keys = ['id', 'psat_id', 'year', 'exam', 'subject', 'number']
        queryset = self.get_problem_queryset()

        if problem_id:
            problem = self.problem_model.objects.get(id=problem_id)
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


class ListViewMixin(BaseMixin):
    def get_filterset(self):
        if self.request.user.is_authenticated:
            return filters.PsatFilter(data=self.request.GET, request=self.request)
        return filters.AnonymousPsatFilter(self.request.GET, request=self.request)


class DetailViewMixin(BaseMixin):
    def get_memo(self, problem_id):
        user_id = self.request.user.id
        if user_id:
            return self.memo_model.objects.filter(user_id=user_id, problem_id=problem_id).first()

    def get_my_tag(self, problem_id):
        user_id = self.request.user.id
        if user_id:
            return self.tag_model.objects.filter(user_id=user_id, problem_id=problem_id).first()

    def get_comments(self, problem_id):
        user_id = self.request.user.id
        if user_id:
            return self.comment_model.objects.filter(problem_id=problem_id).values()

    @staticmethod
    def get_sub_title_from_problem(problem):
        return f'{problem.year}년 {problem.exam} {problem.subject} {problem.number}번'

    def get_find_filter(self, problem_id) -> dict:
        user_id = self.request.user.id
        find_filter = {
            'problem_id': problem_id,
            'user_id': user_id,
        }
        if not user_id:
            find_filter['ip_address'] = self.request.META.get('REMOTE_ADDR')
        return find_filter

    def get_open_instance(self, problem_id):
        find_filter = self.get_find_filter(problem_id)
        with transaction.atomic():
            instance, _ = self.open_model.objects.get_or_create(**find_filter)
            recent_log = self.open_log_model.objects.filter(**find_filter).last()
            if recent_log:
                repetition = recent_log.repetition + 1
            else:
                repetition = 1
            create_filter = find_filter.copy()
            create_filter.update({
                'data_id': instance.id, 'repetition': repetition,
            })
            self.open_log_model.objects.create(**create_filter)

    def get_prev_next_prob(self, problem_id, custom_data) -> tuple:
        if self.request.method == 'GET':
            custom_list = list(custom_data.values_list('id', flat=True))
            prev_prob = next_prob = None
            last_id = len(custom_list) - 1
            try:
                q = custom_list.index(problem_id)
                if q != 0:
                    prev_prob = custom_data[q - 1]
                if q != last_id:
                    next_prob = custom_data[q + 1]
                return prev_prob, next_prob
            except ValueError:
                return None, None


class DetailNavigationViewMixin(BaseMixin):
    @staticmethod
    def get_list_title(view_type):
        list_title_dict = {
            'problem': '',
            'like': '즐겨찾기 추가 문제',
            'rate': '난이도 선택 문제',
            'solve': '정답 확인 문제',
            'memo': '메모 작성 문제',
            'tag': '태그 작성 문제',
        }
        return list_title_dict[view_type]
