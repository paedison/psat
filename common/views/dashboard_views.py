from datetime import datetime

from common import constants
from psat.views import list_views

menu_icon_set = constants.icon.MENU_ICON_SET
color_set = constants.color.COLOR_SET


class DashboardViewSetting(list_views.ListViewSetting):
    menu = 'dashboard'
    url_name = 'dashboard:list'

    @property
    def search_date(self) -> datetime.date:
        search_date = self.request.GET.get('date', '')
        if search_date != '':
            return datetime.strptime(search_date, '%Y-%m-%d').date()
        return search_date

    @property
    def timestamp(self) -> str:
        sort_dict = {
            'like': ('evaluation__liked_at', '-evaluation__liked_at'),
            'rate': ('evaluation__rated_at', '-evaluation__rated_at'),
            'answer': ('evaluation__answered_at', '-evaluation__answered_at'),
        }
        return sort_dict[self.view_type]

    def get_filtered_queryset(self, field='', value=''):
        filtered_queryset = super().get_filtered_queryset(field, value)
        if self.search_date:
            filtered_queryset = filtered_queryset.filter(**{self.timestamp[0]: self.search_date})
        return filtered_queryset.order_by(self.timestamp[1])

    @property
    def info(self) -> dict:
        info = super().info
        info['type'] = f'{self.view_type}Dashboard'
        info['title'] = 'Dashboard'
        info['icon'] = menu_icon_set['dashboard']
        info['color'] = color_set['dashboard']
        info['date'] = self.search_date
        return info

    @property
    def context(self) -> dict:
        return {
            'info': self.info,
            'page_obj': self.page_obj,
            'page_range': self.page_range,
            'like_dashboard': self.view_type == 'like',
            'rate_dashboard': self.view_type == 'rate',
            'answer_dashboard': self.view_type == 'answer',
        }


def base_view(request, view_type='like'):
    dashboard_view_setting = DashboardViewSetting(request, view_type)
    return dashboard_view_setting.rendering()
