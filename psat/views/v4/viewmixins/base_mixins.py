from common.constants import icon_set
from dashboard.models import psat_data_models
from psat import models, utils
from reference.models import psat_models


class ConstantIconSet(icon_set.ConstantIconSet):
    pass


class DefaultModels:
    menu = 'psat'

    # reference.models
    psat_model = psat_models.Psat
    problem_model = psat_models.PsatProblem

    # psat.models
    open_model = models.Open
    like_model = models.Like
    rate_model = models.Rate
    solve_model = models.Solve
    memo_model = models.Memo
    tag_model = models.Tag
    collection_model = models.Collection
    item_model = models.CollectionItem
    comment_model = models.Comment

    # dashboard.models
    open_log_model = psat_data_models.PsatOpenLog
    like_log_model = psat_data_models.PsatLikeLog
    rate_log_model = psat_data_models.PsatRateLog
    solve_log_model = psat_data_models.PsatSolveLog

    request: any
    kwargs: dict
    object: any


class DefaultMethods:
    request: any
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
