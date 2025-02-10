import dataclasses
import traceback
from collections import defaultdict

import django.db.utils
import pandas as pd
from django.db import transaction
from django.db.models import Count, Window, F
from django.db.models.functions import Rank
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy

from common.constants import icon_set_new
from common.decorators import admin_required
from common.utils import HtmxHttpRequest, update_context_data
from ... import models, utils, forms


class ViewConfiguration:
    menu = menu_eng = 'psat'
    menu_kor = 'PSAT'
    submenu = submenu_eng = 'admin'
    submenu_kor = '관리자 메뉴'

    info = {'menu': menu, 'menu_self': submenu}
    icon_menu = icon_set_new.ICON_MENU[menu_eng]
    menu_title = {'kor': menu_kor, 'eng': menu.capitalize()}
    submenu_title = {'kor': submenu_kor, 'eng': submenu.capitalize()}

    url_admin = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_psat_list = reverse_lazy('admin:a_psat_psat_changelist')
    url_admin_problem_list = reverse_lazy('admin:a_psat_problem_changelist')

    url_list = reverse_lazy('psat:admin-list')
    url_psat_create = reverse_lazy('psat:admin-psat-create')
    url_problem_update = reverse_lazy('psat:admin-problem-update')

    url_predict_create = reverse_lazy('psat:admin-predict-create')

    url_study_category_detail = reverse_lazy('psat:admin-study-category-detail')
    url_study_category_create = reverse_lazy('psat:admin-study-category-create')
    url_study_problem_add = reverse_lazy('psat:admin-study-problem-add')

    url_study_curriculum_detail = reverse_lazy('psat:admin-study-curriculum-detail')
    url_study_organization_create = reverse_lazy('psat:admin-study-organization-create')
    url_study_curriculum_create = reverse_lazy('psat:admin-study-curriculum-create')
    url_study_student_add = reverse_lazy('psat:admin-study-student-add')
    url_study_answer_add = reverse_lazy('psat:admin-study-answer-add')


@admin_required
def study_category_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')

    category = get_object_or_404(models.StudyCurriculum, pk=pk)
    category: models.StudyCurriculum
    statistics = models.StudyStatistics.objects.filter(psat__category=category)
    context = update_context_data(config=config, category=category)
    return render(request, 'a_psat/admin_detail.html', context)


@admin_required
def study_curriculum_detail_view(request: HtmxHttpRequest, pk: int):
    config = ViewConfiguration()
    view_type = request.headers.get('View-Type', '')
    page_number = request.GET.get('page', '1')

    curriculum = get_object_or_404(models.StudyCurriculum.objects.get, pk=pk)
    curriculum: models.StudyCurriculum
    statistics = models.StudyStatistics.objects.filter(psat__category=curriculum.category)
    students = models.StudyStudent.objects.filter(curriculum=curriculum)


def bulk_create_or_update(model, list_create, list_update, update_fields):
    model_name = model._meta.model_name
    try:
        with transaction.atomic():
            if list_create:
                model.objects.bulk_create(list_create)
                message = f'Successfully created {len(list_create)} {model_name} instances.'
                is_updated = True
            elif list_update:
                model.objects.bulk_update(list_update, list(update_fields))
                message = f'Successfully updated {len(list_update)} {model_name} instances.'
                is_updated = True
            else:
                message = f'No changes were made to {model_name} instances.'
                is_updated = False
    except django.db.utils.IntegrityError:
        traceback_message = traceback.format_exc()
        print(traceback_message)
        message = f'Error occurred.'
        is_updated = None
    print(message)
    return is_updated
