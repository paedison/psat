import json

from django.http import HttpResponse
from vanilla import ListView, DetailView

from analysis.models import Data, CorrectAnswer


def verify_new_data_exists_or_not():
    with open(r'copy_worksheet.json', 'r', encoding='utf-8') as file:
        content = json.load(file)
        max_id = 0
        for item in content:
            if 'copy_id' in item and isinstance(item['copy_id'], int) and item['copy_id'] > max_id:
                max_id = item['copy_id']
    last_data = Data.objects.all().order_by('id').last()
    try:
        last_data_id = last_data.id
    except AttributeError:
        last_data_id = None
    return max_id == last_data_id


def update_analysis_model():
    is_updated = verify_new_data_exists_or_not()
    message = ''
    if is_updated:
        message = 'Already updated'
    else:
        with open(r'copy_worksheet.json', 'r', encoding='utf-8') as file:
            content = json.load(file)
            for item in content:
                if 'copy_id' in item and isinstance(item['copy_id'], int):
                    Data.objects.create(**item)
                    message = 'Already updated'
                else:
                    message = 'Update failed'
    return HttpResponse(message)


def calculate_total_answer_rate_list(sub_code):
    answer_rate_list = []
    correct_answer_set = CorrectAnswer.correct_answer_set
    for key, item in correct_answer_set.items():
        if key.startswith(f'sub{sub_code}'):
            correct_answer = correct_answer_set[key]
            answer_counts = Data.objects.filter(**{key: correct_answer}).count()
            total_counts = Data.objects.filter(is_valid=True).count()
            answer_rate = answer_counts / total_counts * 100
            answer_rate_list.append(answer_rate)
    return answer_rate_list


def index(request):
    if request.user.is_authenticated:
        message = update_analysis_model()
    else:
        message = 'Not allowed'
    return HttpResponse(message)


class DataListView(ListView):
    model = Data
    template_name = 'analysis/list.html'
    paginate_by = 10


class DataDetailView(DetailView):
    model = Data
    template_name = 'analysis/detail.html'
    context_object_name = 'post'
    lookup_field = 'copy_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total00_answer_list = calculate_total_answer_rate_list('00')
        total01_answer_list = calculate_total_answer_rate_list('01')
        total02_answer_list = calculate_total_answer_rate_list('02')
        total03_answer_list = calculate_total_answer_rate_list('03')
        context['total00_answer_list'] = total00_answer_list
        context['total01_answer_list'] = total01_answer_list
        context['total02_answer_list'] = total02_answer_list
        context['total03_answer_list'] = total03_answer_list
        return context
