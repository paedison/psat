import json

from django.db import transaction
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_mixins import BaseMixin
from ..utils import get_all_ranks_dict, get_all_score_stat_dict


class IndexViewMixIn(ConstantIconSet, BaseMixin):
    sub_title: str
    units: list
    departments: list | None

    participant_count: dict
    answer_predict: dict
    answer_student_count: dict
    answer_student_data: dict
    score_predict: dict

    all_score_stat: dict
    student_score: dict  # score, rank, rank_ratio
    all_answer_rates: dict

    def get_properties(self):
        super().get_properties()

        self.sub_title: str = self.get_sub_title()
        self.units = self.unit_model.objects.filter(exam__abbr=self.ex)
        self.departments = self.get_departments()

        self.participant_count = self.get_participant_count()
        self.answer_predict = self.get_answer_predict()
        self.answer_student_count = self.get_answer_student_count()
        self.answer_student_data = self.get_answer_student_data()

        self.score_predict = self.get_score_predict()

        if self.answer_uploaded and self.student:
            self.all_score_stat = get_all_score_stat_dict(self.get_statistics_qs, self.student)
            all_ranks = get_all_ranks_dict(self.get_statistics_qs, self.user_id)
            self.student_score = self.update_student_score(all_ranks)
            self.all_answer_rates = self.get_all_answer_rates()
        else:
            self.all_score_stat = {'전체': '', '직렬': ''}
            self.student_score = {}
            self.all_answer_rates = {}

    def get_sub_title(self) -> str:
        if self.category == 'PSAT':
            return f'{self.year}년 {self.exam_name} 합격 예측'
        elif self.category == 'Prime':
            return f'제{self.round}회 {self.exam_name} 성적 예측'

    def get_departments(self) -> list:
        if self.category == 'Prime':
            return self.department_model.objects.filter(unit__exam__abbr=self.ex).values()

    def get_participant_count(self):
        participant_count_qs = self.answer_count_model.objects.filter(
            category=self.category,
            year=self.year,
            ex=self.ex,
            round=self.round,
            number=1
        ).values('sub', 'count_total')
        participant_count = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        for query in participant_count_qs:
            sub = query['sub']
            count_total = query['count_total']
            participant_count[sub] = count_total
        return participant_count

    def get_answer_student_count(self) -> dict:
        answers = self.answer_model.objects.filter(student=self.student).values()
        answer_student_count = {}
        for sub, problem_count in self.problem_count_dict.items():
            is_confirmed = False
            answer_count = 0
            for answer in answers:
                if answer['sub'] == sub:
                    is_confirmed = answer['is_confirmed']
                    for i in range(problem_count):
                        number = i + 1
                        if answer[f'prob{number}']:
                            answer_count += 1
            answer_student_count[sub] = {
                'icon': self.ICON_SUBJECT[sub],
                'sub': sub,
                'subject': self.sub_dict[sub],
                'participants': self.participant_count[sub],
                'problem_count': problem_count,
                'answer_count': answer_count,
                'score_predict': 0,
                'is_confirmed': is_confirmed,
            }
        return answer_student_count

    def get_answer_predict(self) -> dict:
        filename = f'{self.base_dir}/score/views/predict_v1/viewmixins/data/answer_predict.json'
        try:
            with open(filename, 'r') as json_file:
                answer_predict = json.load(json_file)
                return answer_predict
        except FileNotFoundError:
            return {'헌법': [], '언어': [], '자료': [], '상황': []}

    def get_answer_student_data(self) -> dict:
        answer_student_data = {}
        all_raw_student_answers = (
            self.answer_model.objects.defer('timestamp').filter(student=self.student).values()
        )
        for raw_student_answers in all_raw_student_answers:
            sub = raw_student_answers['sub']
            answer_student_data[sub] = []

            problem_count = self.problem_count_dict[sub]
            for i in range(problem_count):
                number = i + 1
                answer_student = raw_student_answers[f'prob{number}']
                answer_correct = None
                answer_correct_list = []
                answer_predict_sub = self.answer_predict[sub]

                try:
                    answer_predict = {
                        'ans_number': answer_predict_sub[i]['ans_number'],
                        'rate_accuracy': answer_predict_sub[i]['rate_accuracy'],
                        'rate_selection': answer_predict_sub[i][f'rate_{answer_student}'],
                    }
                except IndexError:
                    answer_predict = {
                        'ans_number': '',
                        'rate_accuracy': '',
                        'rate_selection': '',
                    }

                result = None
                if self.answer_uploaded:
                    answer_correct = self.answer_correct_dict[sub][f'prob{number}']
                    if answer_correct in range(1, 6):
                        result = 'O' if answer_student == answer_correct else 'X'
                    else:
                        answer_correct_list = [int(digit) for digit in str(answer_correct)]
                        result = 'O' if answer_student in answer_correct_list else 'X'
                answer_student_data[sub].append(
                    {
                        'number': number,
                        'answer_correct': answer_correct,
                        'answer_correct_list': answer_correct_list,
                        'answer_predict': answer_predict,
                        'answer_student': answer_student,
                        'result': result,
                    }
                )
        return answer_student_data

    def get_score_predict(self):
        score_dict = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        if self.ex == '칠급':
            score_dict.pop('헌법')
        for sub, score in score_dict.items():
            problem_count = self.problem_count_dict[sub]
            correct_count = 0
            try:
                for ans in self.answer_student_data[sub]:
                    if ans['answer_predict']['ans_number'] == ans['answer_student']:
                        correct_count += 1
            except KeyError:
                pass
            score_dict[sub] = correct_count * 100 / problem_count
        return score_dict

    def get_statistics_qs(self, rank_type='전체'):
        filter_expr = {
            'student__category': self.category,
            'student__year': self.year,
            'student__ex': self.ex,
            'student__round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['student__department_id'] = self.student.department_id
        return self.statistics_model.objects.defer('timestamp').filter(**filter_expr)

    def update_student_score(self, all_ranks):
        rank_total = all_ranks['전체']
        rank_department = all_ranks['직렬']
        try:
            student_score = self.statistics_model.objects.get(student=self.student)  # score, rank, rank_ratio

            student_score.rank_total_heonbeob = rank_total.rank_heonbeob
            student_score.rank_total_eoneo = rank_total.rank_eoneo
            student_score.rank_total_jaryo = rank_total.rank_jaryo
            student_score.rank_total_sanghwang = rank_total.rank_sanghwang
            student_score.rank_total_psat = rank_total.rank_psat

            student_score.rank_ratio_total_heonbeob = rank_total.rank_ratio_heonbeob
            student_score.rank_ratio_total_eoneo = rank_total.rank_ratio_eoneo
            student_score.rank_ratio_total_jaryo = rank_total.rank_ratio_jaryo
            student_score.rank_ratio_total_sanghwang = rank_total.rank_ratio_sanghwang
            student_score.rank_ratio_total_psat = rank_total.rank_ratio_psat

            student_score.rank_department_heonbeob = rank_department.rank_heonbeob
            student_score.rank_department_eoneo = rank_department.rank_eoneo
            student_score.rank_department_jaryo = rank_department.rank_jaryo
            student_score.rank_department_sanghwang = rank_department.rank_sanghwang
            student_score.rank_department_psat = rank_department.rank_psat

            student_score.rank_ratio_department_heonbeob = rank_department.rank_ratio_heonbeob
            student_score.rank_ratio_department_eoneo = rank_department.rank_ratio_eoneo
            student_score.rank_ratio_department_jaryo = rank_department.rank_ratio_jaryo
            student_score.rank_ratio_department_sanghwang = rank_department.rank_ratio_sanghwang
            student_score.rank_ratio_department_psat = rank_department.rank_ratio_psat

            student_score.save()
            return student_score
        except self.statistics_model.DoesNotExist:
            pass

    def get_all_answer_rates(self) -> dict:
        all_answer_count = (
            self.answer_count_model.objects
            .filter(
                category=self.category,
                year=self.year,
                ex=self.ex,
                round=self.round,
            ).order_by('sub', 'number').values()
        )

        all_answer_rates = {'헌법': [], '언어': [], '자료': [], '상황': []}
        for a in all_answer_count:
            sub = a['sub']
            number = a['number']
            answer_correct = self.answer_correct_dict[sub][f'prob{number}']
            if answer_correct in range(1, 6):
                rate_correct = a[f'rate_{answer_correct}']
            else:
                answer_correct_list = [int(digit) for digit in str(answer_correct)]
                rate_correct = sum(a[f'rate_{ans}'] for ans in answer_correct_list)
            all_answer_rates[sub].append(
                {
                    'number': number,
                    'rate_correct': rate_correct,
                }
            )
        return all_answer_rates


class AnswerInputViewMixin(ConstantIconSet, BaseMixin):
    sub_title: str
    sub: str
    subject: str
    answer_student_qs_list: dict
    is_confirmed: bool
    answer_student: list

    def get_properties(self):
        super().get_properties()

        self.sub_title = self.get_sub_title()
        self.sub = self.kwargs.get('sub')
        self.subject = self.sub_dict[self.sub]

        self.answer_student_qs_list = {}
        self.is_confirmed = False
        if self.student:
            answer_student_qs = self.get_answer_student_qs()
            if answer_student_qs:
                self.answer_student_qs_list = self.get_answer_student_qs().values().first()
                self.is_confirmed = self.answer_student_qs_list['is_confirmed']
            self.answer_student = self.get_answer_student_list()

    def get_sub_title(self) -> str:
        if self.round:
            return f'제{self.round}회 {self.exam_name} 성적 예측'
        else:
            return f'{self.year}년 {self.exam_name} 합격 예측'

    def get_answer_student_list(self) -> list:
        answer_student_list = []
        problem_count = self.problem_count_dict[self.sub]
        for i in range(problem_count):
            number = i + 1
            answer_student = ''
            if self.answer_student_qs_list:
                answer_student = self.answer_student_qs_list[f'prob{number}']
            answer_student_list.append(
                {
                    'number': i,
                    'ex': self.ex,
                    'sub': self.sub,
                    'answer_student': answer_student,
                }
            )
        return answer_student_list


class AnswerConfirmViewMixin(ConstantIconSet, BaseMixin):
    sub: str
    is_confirmed: bool
    next_url: str

    def get_properties(self):
        super().get_properties()

        self.sub = self.kwargs.get('sub')
        self.next_url = self.get_next_url()
        self.is_confirmed = self.set_is_confirmed()

    def get_next_url(self):
        answer_sub_list = (
            self.answer_model.objects.filter(student=self.student)
            .distinct().values_list('sub', flat=True)
        )
        for sub in self.sub_dict.keys():
            if sub not in answer_sub_list:
                return reverse_lazy('predict:answer_input', args=[sub])
        return reverse_lazy('predict:index')

    def set_is_confirmed(self):
        try:
            answer_student = self.answer_model.objects.get(student=self.student, sub=self.sub)
            for i in range(1, self.problem_count_dict[self.sub] + 1):
                if getattr(answer_student, f'prob{i}') is None:
                    return False
            with transaction.atomic():
                answer_student.is_confirmed = True
                answer_student.save()
                self.update_answer_count(answer_student)
                answer_predict = self.update_answer_predict()
                self.update_score(answer_student, answer_predict)
            return True
        except self.answer_model.DoesNotExist:
            pass

    def update_answer_count(self, answer_student):
        problem_count = self.problem_count_dict[self.sub]
        with transaction.atomic():
            for i in range(problem_count):
                number = i + 1
                answer = getattr(answer_student, f'prob{number}')
                answer_count, created = self.answer_count_model.objects.get_or_create(
                    category=self.category,
                    year=self.year,
                    ex=self.ex,
                    round=self.round,
                    sub=self.sub,
                    number=number,
                )
                if not created:
                    answer_count.count_total += 1

                for k in range(5):
                    ans_number = k + 1
                    if ans_number == answer:
                        old_count = getattr(answer_count, f'count_{ans_number}')
                        setattr(answer_count, f'count_{ans_number}', old_count + 1)
                        answer_count.save()

    def update_answer_predict(self) -> dict:
        answer_predict = {'헌법': [], '언어': [], '자료': [], '상황': []}
        if self.ex == '칠급':
            answer_predict.pop('헌법')

        all_raw_answer_count = (
            self.answer_count_model.objects.filter(
                category=self.category,
                year=self.year,
                ex=self.ex,
                round=self.round,
            ).order_by('sub', 'number').values()
        )
        for prob in all_raw_answer_count:
            sub = prob['sub']
            answer_count_list = []  # list for counting answers
            for i in range(5):
                ans_number = i + 1
                answer_count_list.append(prob[f'count_{ans_number}'])
            answer_predict_number = answer_count_list.index(max(answer_count_list)) + 1
            answer_predict[sub].append(
                {
                    'ans_number': answer_predict_number,
                    'rate_accuracy': prob[f'rate_{answer_predict_number}'],
                    'rate_1': prob['rate_1'],
                    'rate_2': prob['rate_2'],
                    'rate_3': prob['rate_3'],
                    'rate_4': prob['rate_4'],
                    'rate_5': prob['rate_5'],
                }
            )
        filename = f'{self.base_dir}/score/views/predict_v1/viewmixins/data/answer_predict.json'
        with open(filename, 'w') as json_file:
            json.dump(answer_predict, json_file, indent=2)

        return answer_predict

    def update_score(self, answer_student, answer_predict):
        """ Update scores in PSAT student instances. """
        sub_field = {
            '언어': 'score_eoneo',
            '자료': 'score_jaryo',
            '상황': 'score_sanghwang',
            '헌법': 'score_heonbeob',
        }
        field = sub_field[self.sub]
        ans_predict = answer_predict[self.sub]

        total_count = self.problem_count_dict[self.sub]
        correct_count = 0
        stat, _ = self.statistics_model.objects.get_or_create(student=self.student)

        for i in range(total_count):
            number = i + 1
            if getattr(answer_student, f'prob{number}') == ans_predict[i]['ans_number']:
                correct_count += 1
        score = 100 * correct_count / total_count
        setattr(stat, field, score)

        score_eoneo = stat.score_eoneo or 0
        score_jaryo = stat.score_jaryo or 0
        score_sanghwang = stat.score_sanghwang or 0
        stat.score_psat = score_eoneo + score_jaryo + score_sanghwang
        stat.score_psat_avg = stat.score_psat / 3
        stat.save()
