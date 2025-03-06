from common.constants import icon_set
from common.utils import HtmxHttpRequest
from psat import utils
from psat.models import psat_data_models
from reference.models import psat_models


class ConstantIconSet(icon_set.ConstantIconSet):
    pass


class DefaultModels:
    request: HtmxHttpRequest
    kwargs: dict

    menu = 'psat'

    # reference.models.psat_models
    psat_model = psat_models.Psat
    problem_model = psat_models.PsatProblem

    # psat.models.psat_data_models
    open_model = psat_data_models.Open
    like_model = psat_data_models.Like
    rate_model = psat_data_models.Rate
    solve_model = psat_data_models.Solve
    memo_model = psat_data_models.Memo
    tag_model = psat_data_models.Tag
    collection_model = psat_data_models.Collection
    item_model = psat_data_models.CollectionItem
    comment_model = psat_data_models.Comment

    # dashboard.models.psat_log_models
    # open_log_model = psat_log_models.PsatOpenLog
    # like_log_model = psat_log_models.PsatLikeLog
    # rate_log_model = psat_log_models.PsatRateLog
    # solve_log_model = psat_log_models.PsatSolveLog


class DefaultMethods:
    request: HtmxHttpRequest
    kwargs: dict

    def get_user_id(self):
        if self.request.user.is_authenticated:
            return self.request.user.id

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
