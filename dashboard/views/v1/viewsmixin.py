from django.core.paginator import Paginator
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from dashboard import models as dashboard_models


class DashboardViewMixin(ConstantIconSet):
    """ Represent dashboard view variable. """
    menu = 'dashboard'
    url_name = 'dashboard:list'

    request: any
    kwargs: dict

    user_id: int | None
    view_type: str
    info: dict

    page_obj: any
    open_page_obj: dashboard_models.PsatOpenLog.objects
    like_page_obj: dashboard_models.PsatLikeLog.objects
    rate_page_obj: dashboard_models.PsatRateLog.objects
    solve_page_obj: dashboard_models.PsatSolveLog.objects

    page_range: any
    open_page_range: any
    like_page_range: any
    rate_page_range: any
    solve_page_range: any

    pagination_url: str
    open_pagination_url: str
    like_pagination_url: str
    rate_pagination_url: str
    solve_pagination_url: str

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None
        self.view_type = self.kwargs.get('view_type', 'open')

        self.page_obj, self.page_range = self.get_list_paginator_info()
        self.open_page_obj, self.open_page_range = self.get_paginator_info('open')
        self.like_page_obj, self.like_page_range = self.get_paginator_info('like')
        self.rate_page_obj, self.rate_page_range = self.get_paginator_info('rate')
        self.solve_page_obj, self.solve_page_range = self.get_paginator_info('solve')

        self.pagination_url = self.get_list_pagination_url()
        self.open_pagination_url = self.get_pagination_url('open')
        self.like_pagination_url = self.get_pagination_url('like')
        self.rate_pagination_url = self.get_pagination_url('rate')
        self.solve_pagination_url = self.get_pagination_url('solve')

        self.info = {
            'menu': self.menu,
            'view_type': self.view_type,
        }

    def get_logs(self, view_type: str):
        model_dict = {
            'open': dashboard_models.PsatOpenLog,
            'like': dashboard_models.PsatLikeLog,
            'rate': dashboard_models.PsatRateLog,
            'solve': dashboard_models.PsatSolveLog,
        }
        model = model_dict[view_type]
        return (
            model.objects.filter(user_id=self.user_id).order_by('-timestamp')
            .select_related('problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
        )

    def get_paginator_info(self, view_type: str) -> tuple:
        """ Get paginator, elided page range for each view type in DashboardMainView. """
        logs = self.get_logs(view_type)
        paginator = Paginator(logs, 5)
        page_obj = paginator.get_page(1)
        page_range = paginator.get_elided_page_range(number=1, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_pagination_url(self, view_type: str) -> str:
        return reverse_lazy(self.url_name, args=[view_type])

    def get_list_paginator_info(self) -> tuple:
        """ Get paginator, elided page range in DashboardListView. """
        logs = self.get_logs(self.view_type)
        page_number = self.request.GET.get('page', 1)

        paginator = Paginator(logs, 5)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_list_pagination_url(self) -> str:
        return reverse_lazy(self.url_name, args=[self.view_type])
