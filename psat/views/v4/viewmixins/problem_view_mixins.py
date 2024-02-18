from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse_lazy

from dashboard.models import psat_data_models
from psat import models as custom_models
from psat.views.v4 import filters
from reference.models import psat_models as reference_models
from . import base_mixins


class ListViewMixin(base_mixins.BaseMixin):
    page_obj: any
    page_range: any

    def get_properties(self):
        super().get_properties()

        self.page_obj, self.page_range = self.get_paginator_info()

    def get_filterset(self):
        if self.request.user.is_authenticated:
            return filters.PsatFilter(data=self.request.GET, request=self.request)
        return filters.AnonymousPsatFilter(self.request.GET, request=self.request)

    def get_queryset(self):
        return self.get_filterset().qs

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        queryset = self.get_queryset()

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(number=self.page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range


class DetailViewMixin(base_mixins.BaseMixin):
    memo: custom_models.Memo
    my_tag: custom_models.Tag
    comments: custom_models.Comment

    prev_prob: reference_models.PsatProblem.objects
    next_prob: reference_models.PsatProblem.objects
    list_data: list

    def get_properties(self):
        super().get_properties()

        self.memo = custom_models.Memo.objects.none()
        self.my_tag = custom_models.Tag.objects.none()
        self.comments = custom_models.Comment.objects.none()
        if self.request.user.is_authenticated:
            self.memo = custom_models.Memo.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
            self.my_tag = custom_models.Tag.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
            self.comments = custom_models.Comment.objects.filter(problem_id=self.problem_id).values()

        view_custom_data = self.custom_data[self.view_type]
        self.prev_prob, self.next_prob = self.get_prev_next_prob(view_custom_data)
        self.list_data = get_list_data(view_custom_data)

    def get_sub_title(self):
        year = self.problem.year
        exam = self.problem.exam
        subject = self.problem.subject
        number = self.problem.number
        return f'{year}년 {exam} {subject} {number}번'

    def get_find_filter(self) -> dict:
        find_filter = {
            'problem_id': self.problem_id,
            'user_id': self.user_id,
        }
        if not self.user_id:
            find_filter['ip_address'] = self.ip_address
        return find_filter

    def get_open_instance(self):
        find_filter = self.get_find_filter()
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

    def get_prev_next_prob(self, custom_data: reference_models.PsatProblem.objects) -> tuple:
        if self.request.method == 'GET':
            custom_list = list(custom_data.values_list('id', flat=True))
            prev_prob = next_prob = None
            last_id = len(custom_list) - 1
            try:
                q = custom_list.index(self.problem_id)
                if q != 0:
                    prev_prob = custom_data[q - 1]
                if q != last_id:
                    next_prob = custom_data[q + 1]
                return prev_prob, next_prob
            except ValueError:
                return None, None


class DetailNavigationViewMixin(base_mixins.BaseMixin):
    problem: reference_models.PsatProblem.objects
    list_data: list
    list_title: str

    def get_properties(self):
        super().get_properties()

        view_custom_data = self.custom_data[self.view_type]
        self.list_data = get_list_data(view_custom_data)
        self.list_title = self.get_list_title()

    def get_list_title(self):
        list_title_dict = {
            'problem': '',
            'like': '즐겨찾기 추가 문제',
            'rate': '난이도 선택 문제',
            'solve': '정답 확인 문제',
            'memo': '메모 작성 문제',
            'tag': '태그 작성 문제',
        }
        return list_title_dict[self.view_type]


def get_list_data(custom_data) -> list:
    def get_view_list_data():
        organized_dict = {}
        organized_list = []
        for prob in custom_data:
            key = prob['psat_id']
            if key not in organized_dict:
                organized_dict[key] = []
            year, exam, subject = prob['year'], prob['exam'], prob['subject']
            problem_url = reverse_lazy('psat:detail', args=[prob['id']])
            list_item = {
                'exam_name': f"{year}년 {exam} {subject}",
                'problem_number': prob['number'],
                'problem_id': prob['id'],
                'problem_url': problem_url
            }
            organized_dict[key].append(list_item)

        for key, items in organized_dict.items():
            num_empty_instances = 5 - (len(items) % 5)
            if num_empty_instances < 5:
                items.extend([None] * num_empty_instances)
            for i in range(0, len(items), 5):
                row = items[i:i+5]
                organized_list.extend(row)
        return organized_list
    return get_view_list_data()
