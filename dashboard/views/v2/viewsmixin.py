from django.db.models import F
from django.http import HttpRequest
from django_htmx.middleware import HtmxDetails

from common.constants.icon_set import ConstantIconSet
from dashboard import utils
from dashboard.models import psat_log_models
from psat.models import data_models


class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


class DefaultModels:
    menu = 'dashboard'

    # psat.models
    open_model = data_models.Open
    like_model = data_models.Like
    rate_model = data_models.Rate
    solve_model = data_models.Solve
    memo_model = data_models.Memo
    tag_model = data_models.Tag
    collection_model = data_models.Collection
    item_model = data_models.CollectionItem
    comment_model = data_models.Comment

    # dashboard.models
    open_log_model = psat_log_models.PsatOpenLog
    like_log_model = psat_log_models.PsatLikeLog
    rate_log_model = psat_log_models.PsatRateLog
    solve_log_model = psat_log_models.PsatSolveLog

    request: HtmxHttpRequest
    kwargs: dict


class DashboardViewMixin(
    ConstantIconSet,
    DefaultModels,
):
    """ Represent dashboard view variable. """

    def get_info(self, view_type):
        return {
            'menu': self.menu,
            'view_type': view_type,
        }

    def get_user_id(self):
        if self.request.user.is_authenticated:
            return self.request.user.id

    def get_view_type(self):
        return self.kwargs.get('view_type', 'open')

    def get_page_number(self):
        return self.request.GET.get('page', '1')

    def get_unique(self):
        unique = self.request.GET.get('unique', 'None')
        unique_dict = {
            'None': None,
            'True': True,
            'False': False,
        }
        return unique_dict[unique]

    def get_log_dict(self, user_id: str, unique: str):
        def get_queryset(model):
            return (
                model.objects.filter(user_id=user_id)
                .select_related('problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
                .annotate(
                    year=F('problem__psat__year'),
                    ex=F('problem__psat__exam__abbr'),
                    exam=F('problem__psat__exam__name'),
                    sub=F('problem__psat__subject__abbr'),
                    subject=F('problem__psat__subject__name'),
                    number=F('problem__number'),
                    question=F('problem__question'),
                )
            )

        if unique:
            return {
                'open': get_queryset(self.open_model).order_by('-updated_at'),
                'like': get_queryset(self.like_model).order_by('-updated_at'),
                'rate': get_queryset(self.rate_model).order_by('-updated_at'),
                'solve': get_queryset(self.solve_model).order_by('-updated_at'),
            }
        else:
            return {
                'open': get_queryset(self.open_log_model).order_by('-timestamp'),
                'like': get_queryset(self.like_log_model).order_by('-timestamp'),
                'rate': get_queryset(self.rate_log_model).order_by('-timestamp'),
                'solve': get_queryset(self.solve_log_model).order_by('-timestamp'),
            }

    @staticmethod
    def get_url_options(page_number, unique):
        return f'page={page_number}&unique={unique}'

    def get_paginator_info(self, page_data, per_page=5) -> tuple:
        """ Get paginator, elided page range for each view type in MainView. """
        page_number = self.get_page_number()
        return utils.get_page_obj_and_range(page_number, page_data, per_page)
