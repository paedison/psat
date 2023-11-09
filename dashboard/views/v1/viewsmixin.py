from django.core.paginator import Paginator
from django.urls import reverse_lazy

from dashboard.models import (
    PsatOpenLog,
    PsatLikeLog,
    PsatRateLog,
    PsatSolveLog,
)


class DashboardViewMixin:
    """ Represent dashboard view variable. """
    menu = 'dashboard'
    url_name = 'dashboard:list'
    request: any
    kwargs: dict

    @property
    def user_id(self) -> int:
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        return user_id

    @property
    def view_type(self) -> str:
        """Get view type from [ problem, like, rate, solve ]. """
        return self.kwargs.get('view_type', 'open')

    def get_logs(self, view_type: str):
        model_dict = {
            'open': PsatOpenLog,
            'like': PsatLikeLog,
            'rate': PsatRateLog,
            'solve': PsatSolveLog,
        }
        model = model_dict[view_type]
        return (
            model.objects.filter(user_id=self.user_id).order_by('-timestamp')
            .select_related('problem', 'problem__psat', 'problem__psat__exam', 'problem__psat__subject')
        )

    def get_paginator_info(self, view_type: str) -> tuple[object, object]:
        """ Get paginator, elided page range for each view type in DashboardMainView. """
        logs = self.get_logs(view_type)
        paginator = Paginator(logs, 5)
        page_obj = paginator.get_page(1)
        page_range = paginator.get_elided_page_range(number=1, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_pagination_url(self, view_type: str) -> str:
        return reverse_lazy(self.url_name, args=[view_type])

    def get_list_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range in DashboardListView. """
        logs = self.get_logs(self.view_type)
        page_number = self.request.GET.get('page', 1)

        paginator = Paginator(logs, 5)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(number=page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range

    def get_list_pagination_url(self) -> str:
        return reverse_lazy(self.url_name, args=[self.view_type])
