from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from vanilla import TemplateView

from .viewmixins.list_viewmixins import ScoreListViewMixin


class BaseView(
    LoginRequiredMixin,
    ScoreListViewMixin,
    TemplateView
):
    """ Represent information related PsatTemporaryAnswer and PsatConfirmedAnswer models. """
    menu = 'score'
    view_type = 'primeScore'
    template_name = 'score/prime/score_list.html'
    login_url = settings.LOGIN_URL

    request: any

    def get_template_names(self) -> str:
        """
        Get the template name.
        base(GET): whole page > main(POST): main page > content(GET): content page
        :return: str
        """
        base_template = self.template_name
        main_template = f'{base_template}#list_main'
        if self.request.method == 'GET':
            return main_template if self.request.htmx else base_template
        else:
            return main_template

    def post(self, request, *args, **kwargs):
        return super().get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        page_obj, page_range = self.get_paginator_info()
        info = {
            'menu': self.menu,
            'view_type': self.view_type,
        }
        context = {
            'info': info,
            'title': 'Score',
            'icon': '<i class="fa-solid fa-chart-simple fa-fw"></i>',
            'page_obj': page_obj,
            'page_range': page_range,

            # Icons
            'icon_menu': self.ICON_MENU,
            'icon_subject': self.ICON_SUBJECT,
        }
        return context


base_view = BaseView.as_view()
