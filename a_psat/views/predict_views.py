import json
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_not_required
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django_htmx.http import retarget, reswap, push_url

from common.constants import icon_set_new
from common.utils import HtmxHttpRequest, update_context_data
from .. import models


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'predict'
    submenu_kor = '합격예측'
    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    psat_year = 2024
    psat_exam = '행시'

    url_admin = reverse_lazy('admin:a_psat_predict_changelist')
    url_list = reverse_lazy('psat:predict-index')

    def get_psat(self):
        return get_object_or_404(models.PredictPsat, psat__year=self.psat_year, psat__exam=self.psat_exam)


@login_not_required
def index_view(request: HtmxHttpRequest):
    config = ViewConfiguration()
    context = update_context_data(
        info=config.info, current_time=timezone.now(), title='PSAT',
        sub_title='합격 예측', icon_menu=icon_set_new.ICON_MENU['psat'])
    return render(request, 'a_psat/predict/predict_index.html', context)
