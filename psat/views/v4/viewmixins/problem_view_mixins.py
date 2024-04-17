from django.db import transaction

from dashboard.models import psat_data_models
from psat import models as custom_models
from psat.utils import get_page_obj_and_range
from psat.views.v4 import filters
from reference.models import psat_models as reference_models
from . import base_mixins


class ListViewMixin(base_mixins.BaseMixin):
    def get_filterset(self):
        if self.request.user.is_authenticated:
            return filters.PsatFilter(data=self.request.GET, request=self.request)
        return filters.AnonymousPsatFilter(self.request.GET, request=self.request)

    def get_paginator_info(self, page_data, per_page=10) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.request.GET.get('page', '1')
        return get_page_obj_and_range(page_number, page_data, per_page)


class DetailViewMixin(base_mixins.BaseMixin):
    def get_memo(self, problem_id):
        user_id = self.get_user_id()
        memo = custom_models.Memo.objects.none()
        if user_id:
            memo = custom_models.Memo.objects.filter(user_id=user_id, problem_id=problem_id).first()
        return memo

    def get_my_tag(self, problem_id):
        user_id = self.get_user_id()
        my_tag = custom_models.Tag.objects.none()
        if user_id:
            my_tag = custom_models.Tag.objects.filter(user_id=user_id, problem_id=problem_id).first()
        return my_tag

    def get_comments(self, problem_id):
        user_id = self.get_user_id()
        comments = custom_models.Comment.objects.none()
        if user_id:
            comments = custom_models.Comment.objects.filter(problem_id=problem_id).values()
        return comments

    @staticmethod
    def get_sub_title_from_problem(problem):
        return f'{problem.year}년 {problem.exam} {problem.subject} {problem.number}번'

    def get_find_filter(self, problem_id) -> dict:
        user_id = self.get_user_id()
        find_filter = {
            'problem_id': problem_id,
            'user_id': user_id,
        }
        if not user_id:
            find_filter['ip_address'] = self.get_ip_address()
        return find_filter

    def get_open_instance(self, problem_id):
        find_filter = self.get_find_filter(problem_id)
        with transaction.atomic():
            instance, is_created = custom_models.Open.objects.get_or_create(**find_filter)
            recent_log = psat_data_models.PsatOpenLog.objects.filter(**find_filter).last()
            if recent_log:
                repetition = recent_log.repetition + 1
            else:
                repetition = 1
            create_filter = find_filter.copy()
            extra_filter = {
                'data_id': instance.id,
                'repetition': repetition,
            }
            create_filter.update(extra_filter)
            psat_data_models.PsatOpenLog.objects.create(**create_filter)

    def get_prev_next_prob(self, problem_id, custom_data: reference_models.PsatProblem.objects) -> tuple:
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


class DetailNavigationViewMixin(base_mixins.BaseMixin):
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
