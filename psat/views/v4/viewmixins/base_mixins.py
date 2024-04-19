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

    @staticmethod
    def get_url(name, *args):
        return utils.get_url(name, *args)

    @staticmethod
    def get_problem_from_problem_id(problem_id):
        return utils.get_problem_from_problem_id(problem_id)

    @staticmethod
    def get_problem_queryset():
        return utils.get_problem_queryset()

    @staticmethod
    def get_list_data(view_custom_data):
        return utils.get_list_data(view_custom_data)

    @staticmethod
    def get_max_order(existing_collections):
        return utils.get_max_order(existing_collections)

    @staticmethod
    def get_new_ordering(collections):
        return utils.get_new_ordering(collections)

    @staticmethod
    def get_problem_by_problem_id(problem_id: str):
        if problem_id:
            return (
                psat_models.PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
                .select_related('psat', 'psat__exam', 'psat__subject')
                .prefetch_related('likes', 'rates', 'solves')
                .get(id=problem_id)
            )

    def get_page_number(self):
        return self.request.GET.get('page', '1')

    def get_paginator_info(self, page_data, per_page=10) -> tuple:
        """ Get paginator, elided page range, and collect the evaluation info. """
        page_number = self.get_page_number()
        return utils.get_page_obj_and_range(page_number, page_data, per_page)
