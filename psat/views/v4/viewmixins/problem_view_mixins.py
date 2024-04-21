from django.db import models, transaction

from psat import utils
from psat.views.v4 import filters
from . import base_mixins


class BaseMixin(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    menu = 'psat'
    color_dict = {
        'problem': 'primary',
        'like': 'danger',
        'rate': 'warning',
        'solve': 'success',
        'search': 'primary',
        'memo': 'warning',
        'tag': 'primary',
    }

    def get_view_type(self) -> str:
        return self.kwargs.get('view_type', 'problem')

    def get_keyword(self) -> str:
        return self.request.GET.get('keyword', '') or self.request.POST.get('keyword', '')

    def get_exam_reference(self) -> dict:
        return {
            'year': self.request.GET.get('year', ''),
            'ex': self.request.GET.get('ex', ''),
            'sub': self.request.GET.get('sub', ''),
        }

    def get_custom_options(self) -> dict:
        return {
            'likes': self.request.GET.get('likes', ''),
            'rates': self.request.GET.get('rates', ''),
            'solves': self.request.GET.get('solves', ''),
            'memos': self.request.GET.get('memos', ''),
            'tags': self.request.GET.get('tags', ''),
        }

    def get_psat_by_exam_reference(self, exam_reference):
        psat_filter = models.Q()
        year, ex, sub = exam_reference['year'], exam_reference['ex'], exam_reference['sub']
        if year:
            psat_filter &= models.Q(year=year)
        if ex:
            psat_filter &= models.Q(exam__abbr=ex)
        if sub:
            psat_filter &= models.Q(subject__abbr=sub)
        return self.psat_model.objects.filter(psat_filter).select_related('exam', 'subject').first()

    @staticmethod
    def get_sub_title_by_psat(psat, exam_reference, end_string='기출문제') -> str:
        return utils.get_sub_title_by_psat(psat, exam_reference, end_string)

    def get_info_by_view_type(self, view_type) -> dict[str, str]:
        """ Get the meta-info for the current view. """
        return {
            'menu': 'psat',
            'view_type': view_type,
            'color': self.color_dict[view_type],
        }

    def get_custom_data(self, user_id, problem_id=None) -> dict:
        """ Get all kinds of custom data. """
        values_list_keys = ['id', 'psat_id', 'year', 'exam', 'subject', 'number']
        problem_data = like_data = rate_data = solve_data = memo_data = tag_data = collection_data = comment_data = None

        queryset = utils.get_problem_queryset()

        if problem_id:
            problem = self.problem_model.objects.get(id=problem_id)
            problem_data = queryset.filter(psat=problem.psat).values(*values_list_keys)
        if user_id:
            queryset = queryset.prefetch_related('likes', 'rates', 'solves')
            like_data = utils.get_custom_data_like(user_id, queryset, values_list_keys)
            rate_data = utils.get_custom_data_rate(user_id, queryset, values_list_keys)
            solve_data = utils.get_custom_data_solve(user_id, queryset, values_list_keys)
            memo_data = utils.get_custom_data_memo(user_id, queryset, values_list_keys)
            tag_data = utils.get_custom_data_tag(user_id, queryset, values_list_keys)
            collection_data = utils.get_custom_data_collection(user_id, queryset, values_list_keys)
            comment_data = utils.get_custom_data_comment(user_id, queryset, values_list_keys)

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
    def get_filterset_by_user_id(self, user_id):
        if user_id:
            return filters.PsatFilter(data=self.request.GET, request=self.request)
        return filters.AnonymousPsatFilter(self.request.GET, request=self.request)


class DetailViewMixin(BaseMixin):
    def get_open_instance(self, user_id, problem_id):
        find_filter = self.get_find_filter_by_problem_id(user_id, problem_id)
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
    list_title_dict = {
        'problem': '',
        'like': '즐겨찾기 추가 문제',
        'rate': '난이도 선택 문제',
        'solve': '정답 확인 문제',
        'memo': '메모 작성 문제',
        'tag': '태그 작성 문제',
    }
