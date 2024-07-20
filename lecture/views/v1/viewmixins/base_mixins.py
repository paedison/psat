from common.constants import icon_set
from common.utils import HtmxHttpRequest
from lecture import utils
from lecture.models import lecture_models, custom_models
from reference.models import psat_models


class ConstantIconSet(icon_set.ConstantIconSet):
    pass


class DefaultModels:
    request: HtmxHttpRequest
    kwargs: dict

    menu = 'lecture'

    # reference.models.psat_models
    psat_model = psat_models.Psat
    problem_model = psat_models.PsatProblem

    # lecture.models.lecture_models
    lecture_model = lecture_models.Lecture

    # lecture.models.custom_models
    memo_model = custom_models.Memo
    tag_model = custom_models.Tag
    comment_model = custom_models.Comment


class DefaultMethods:
    request: HtmxHttpRequest
    kwargs: dict

    @property
    def lecture_id(self):
        return self.kwargs.get('lecture_id')

    def get_user_id(self):
        if self.request.user.is_authenticated:
            return self.request.user.id

    @staticmethod
    def get_lecture(lecture_id):
        return lecture_models.Lecture.objects.select_related('subject').get(pk=lecture_id)

    def get_page_number(self):
        return self.request.GET.get('page', '1')

    def get_paginator_info(self, page_data, per_page=10) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.get_page_number()
        return utils.get_page_obj_and_range(page_number, page_data, per_page)

    def get_find_filter_by_problem_id(self, user_id, problem_id) -> dict:
        find_filter = {
            'problem_id': problem_id,
            'user_id': user_id,
        }
        if not user_id:
            find_filter['ip_address'] = self.request.META.get('REMOTE_ADDR')
        return find_filter
