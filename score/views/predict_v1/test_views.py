from score.views.predict_v1.normal_views import IndexView


class TestView(IndexView):
    template_name = 'score/predict_v1/predict_test.html'


data_answer = {
    'answer_correct': {
        '헌법': [
            {'ans_number': 0, 'ans_number_list': [], 'number': '0', 'rate_correct': 0},
            {'ans_number': 0, 'ans_number_list': [], 'number': '0', 'rate_correct': 0},
            {'ans_number': 0, 'ans_number_list': [], 'number': '0', 'rate_correct': 0},
            {'ans_number': 0, 'ans_number_list': [], 'number': '0', 'rate_correct': 0},
        ],
        '언어': [],
        '자료': [],
        '상황': [],
    },
    'answer_predict': {},
    'answer_student': {},
}
