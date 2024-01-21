from django.db import transaction
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_mixins import BaseMixin
from ..utils import get_all_ranks_dict, get_all_score_stat_dict


class IndexViewMixIn(ConstantIconSet, BaseMixin):
    sub_title: str
    units: list
    departments: list | None

    all_answer_count: list
    dataset_answer_student: list
    participant_count: dict
    info_answer_student: dict

    data_answer: dict
    score_virtual_student: dict

    all_score_stat: dict
    score_student: dict  # score, rank, rank_ratio
    all_answer_rates: dict

    def get_properties(self):
        super().get_properties()

        self.sub_title: str = self.get_sub_title()
        self.units = self.unit_model.objects.filter(exam__abbr=self.ex)
        self.departments = self.get_departments()

        self.all_answer_count = self.get_all_answer_count()
        self.dataset_answer_student = self.get_dataset_answer_student()
        self.participant_count = self.get_participant_count()
        self.info_answer_student = self.get_info_answer_student()

        self.data_answer = self.get_data_answer()
        self.score_virtual_student = self.update_score_virtual_student()

        if self.answer_uploaded and self.student:
            self.update_score_real_student()
            self.all_score_stat = get_all_score_stat_dict(self.get_statistics_qs, self.student)
            all_ranks = get_all_ranks_dict(self.get_statistics_qs, self.user_id)
            self.score_student = self.update_score_student(all_ranks)
        else:
            self.all_score_stat = {'전체': '', '직렬': ''}
            self.score_student = {}
            self.all_answer_rates = {}

    def get_sub_title(self) -> str:
        if self.category == 'PSAT':
            return f'{self.year}년 {self.exam_name} 합격 예측'
        elif self.category == 'Prime':
            return f'제{self.round}회 {self.exam_name} 성적 예측'

    def get_departments(self) -> list:
        return self.department_model.objects.filter(unit__exam__abbr=self.ex).values()

    def get_all_answer_count(self) -> list:
        return (
            self.answer_count_model.objects.filter(
                category=self.category,
                year=self.year,
                ex=self.ex,
                round=self.round
            ).order_by('sub', 'number').values()
        )

    def get_dataset_answer_student(self) -> list:
        return self.answer_model.objects.defer('timestamp').filter(student=self.student).values()

    def get_participant_count(self):
        participant_count = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        if self.ex == '칠급':
            participant_count.pop('헌법')
        participant_count_qs = self.answer_count_model.objects.filter(
            category=self.category,
            year=self.year,
            ex=self.ex,
            round=self.round,
            number=1
        ).values('sub', 'count_total')
        for query in participant_count_qs:
            sub = query['sub']
            count_total = query['count_total']
            participant_count[sub] = count_total
        return participant_count

    def get_info_answer_student(self) -> dict:
        info_answer_student = {}
        for sub, problem_count in self.problem_count_dict.items():
            is_confirmed = False
            answer_count = 0
            for dataset_answer in self.dataset_answer_student:
                if dataset_answer['sub'] == sub:
                    is_confirmed = dataset_answer['is_confirmed']
                    for i in range(problem_count):
                        number = i + 1
                        if dataset_answer[f'prob{number}']:
                            answer_count += 1
            info_answer_student[sub] = {
                'icon': self.ICON_SUBJECT[sub],
                'sub': sub,
                'subject': self.sub_dict[sub],
                'participants': self.participant_count[sub],
                'problem_count': problem_count,
                'answer_count': answer_count,
                'score_predict': 0,
                'is_confirmed': is_confirmed,
            }
        info_answer_student['psat'] = {
            'icon': '',
            'sub': 'PSAT',
            'subject': 'PSAT 평균',
            'participants': (
                max(
                    info_answer_student['헌법']['participants'],
                    info_answer_student['언어']['participants'],
                    info_answer_student['자료']['participants'],
                    info_answer_student['상황']['participants'],
                )
            ),
            'problem_count': sum(self.problem_count_dict.values()),
            'answer_count': (
                sum(
                    [
                        info_answer_student['헌법']['answer_count'],
                        info_answer_student['언어']['answer_count'],
                        info_answer_student['자료']['answer_count'],
                        info_answer_student['상황']['answer_count'],
                    ]
                )
            ),
            'score_predict': (
                sum(
                    [
                        info_answer_student['헌법']['score_predict'],
                        info_answer_student['언어']['score_predict'],
                        info_answer_student['자료']['score_predict'],
                        info_answer_student['상황']['score_predict'],
                    ]
                )
            ) / 3,
            'is_confirmed': all(
                [
                    info_answer_student['헌법']['is_confirmed'],
                    info_answer_student['언어']['is_confirmed'],
                    info_answer_student['자료']['is_confirmed'],
                    info_answer_student['상황']['is_confirmed'],
                ]
            ),
        }
        return info_answer_student

    def get_data_answer(self) -> dict:
        """
        data_answer_correct: 정답
        data_answer_predict: 예상 정답
        data_answer_student: 선택 답안
        """
        data_answer_correct = self.answer_correct_dict.copy()
        data_answer_predict = {'헌법': [], '언어': [], '자료': [], '상황': []}
        data_answer_student = {'헌법': [], '언어': [], '자료': [], '상황': []}
        if self.ex == '칠급':
            data_answer_predict.pop('헌법')
            data_answer_student.pop('헌법')

        for a in self.all_answer_count:
            # data_answer_correct
            sub = a['sub']  # 과목
            number = a['number']  # 문제 번호

            if self.answer_uploaded:
                prob = data_answer_correct[sub][number - 1]
                ans_number_correct = prob['ans_number']

                if ans_number_correct in range(1, 6):
                    ans_number_list = []
                    rate_correct = a[f'rate_{ans_number_correct}']
                else:
                    ans_number_list = [int(digit) for digit in str(ans_number_correct)]
                    rate_correct = sum(a[f'rate_{ans}'] for ans in ans_number_list)
                prob.update(
                    {
                        'ans_number_list': ans_number_list,
                        'rate_correct': rate_correct,
                    }
                )

            # data_answer_predict
            answer_count_list = []  # list for counting answers
            for i in range(5):
                answer_count_list.append(a[f'count_{i + 1}'])
            ans_number_predict = answer_count_list.index(max(answer_count_list)) + 1  # 예상 정답
            rate_accuracy = a[f'rate_{ans_number_predict}']  # 정확도
            data_answer_predict[sub].append(
                {
                    'number': number,
                    'ans_number': ans_number_predict,
                    'rate_accuracy': rate_accuracy,
                }
            )

        # data_answer_student
        for dataset_answer in self.dataset_answer_student:
            sub = dataset_answer['sub']
            problem_count = self.problem_count_dict[sub]
            for i in range(problem_count):
                number = i + 1
                ans_number_student = dataset_answer[f'prob{number}']

                result = ''
                if self.answer_uploaded:
                    ans_number_correct = data_answer_correct[sub][i]['ans_number']
                    ans_number_list_correct = data_answer_correct[sub][i]['ans_number_list']
                    if ans_number_correct in range(1, 6):
                        result = 'O' if ans_number_student == ans_number_correct else 'X'
                    else:
                        result = 'O' if ans_number_student in ans_number_list_correct else 'X'

                rate_selection = 0
                for a in self.all_answer_count:
                    if sub == a['sub'] and number == a['number']:
                        rate_selection = a[f'rate_{ans_number_student}']
                data_answer_student[sub].append(
                    {
                        'number': number,
                        'ans_number': ans_number_student,
                        'result': result,
                        'rate_selection': rate_selection,
                    }
                )

        return {
            'answer_correct': data_answer_correct,
            'answer_predict': data_answer_predict,
            'answer_student': data_answer_student,
        }

    def update_score_virtual_student(self) -> dict:
        score_dict = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        if self.ex == '칠급':
            score_dict.pop('헌법')

        for sub, score in score_dict.items():
            problem_count = self.problem_count_dict[sub]
            correct_count = 0
            for i in range(problem_count):
                answer_predict = None
                answer_student = None

                answer_predict_sub = self.data_answer['answer_predict'][sub]
                if answer_predict_sub:
                    answer_predict = answer_predict_sub[i]['ans_number']

                answer_student_sub = self.data_answer['answer_student'][sub]
                if answer_student_sub:
                    answer_student = answer_student_sub[i]['ans_number']

                if answer_predict and answer_student and answer_predict == answer_student:
                    correct_count += 1
            score_dict[sub] = correct_count * 100 / problem_count

        score_dict['psat'] = sum([score_dict['언어'], score_dict['자료'], score_dict['상황']])
        score_dict['psat_avg'] = score_dict['psat'] / 3

        with transaction.atomic():
            score_virtual_student, _ = self.statistics_virtual_model.objects.get_or_create(student=self.student)
            for sub, score in score_dict.items():
                field = self.sub_field[sub]
                setattr(score_virtual_student, field, score_dict[sub])
            score_virtual_student.save()
        return score_dict

    def update_score_real_student(self):
        if self.answer_uploaded:
            score_dict = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
            if self.ex == '칠급':
                score_dict.pop('헌법')

            for sub, score in score_dict.items():
                problem_count = self.problem_count_dict[sub]
                correct_count = 0
                for i in range(problem_count):
                    answer_correct = None
                    answer_student = None

                    answer_correct_sub = self.answer_correct_dict[sub]
                    if answer_correct_sub:
                        answer_correct = answer_correct_sub[i]['ans_number']

                    answer_student_sub = self.data_answer['answer_student'][sub]
                    if answer_student_sub:
                        answer_student = answer_student_sub[i]['ans_number']

                    if answer_correct <= 5 and answer_correct == answer_student:
                        correct_count += 1
                    if answer_correct > 5:
                        answer_correct_list = [int(digit) for digit in str(answer_correct)]
                        if answer_student in answer_correct_list:
                            correct_count += 1
                score_dict[sub] = correct_count * 100 / problem_count

            score_dict['psat'] = sum([score_dict['언어'], score_dict['자료'], score_dict['상황']])
            score_dict['psat_avg'] = score_dict['psat'] / 3

            with transaction.atomic():
                score_real_student, _ = self.statistics_model.objects.get_or_create(student=self.student)
                for sub, score in score_dict.items():
                    field = self.sub_field[sub]
                    setattr(score_real_student, field, score_dict[sub])
                score_real_student.save()

    def get_statistics_virtual_qs(self, rank_type='전체'):
        filter_expr = {
            'student__category': self.category,
            'student__year': self.year,
            'student__ex': self.ex,
            'student__round': self.round,
        }
        if rank_type == '직렬':
            if self.student:
                filter_expr['student__department_id'] = self.student.department_id
        return self.statistics_virtual_model.objects.defer('timestamp').filter(**filter_expr)

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

    def update_score_student(self, all_ranks):
        rank_total = all_ranks['전체']
        rank_department = all_ranks['직렬']
        score_student, _ = self.statistics_model.objects.get_or_create(student=self.student)  # score, rank, rank_ratio
        score_student.rank_total_heonbeob = rank_total.rank_heonbeob
        score_student.rank_total_eoneo = rank_total.rank_eoneo
        score_student.rank_total_jaryo = rank_total.rank_jaryo
        score_student.rank_total_sanghwang = rank_total.rank_sanghwang
        score_student.rank_total_psat = rank_total.rank_psat

        score_student.rank_ratio_total_heonbeob = rank_total.rank_ratio_heonbeob
        score_student.rank_ratio_total_eoneo = rank_total.rank_ratio_eoneo
        score_student.rank_ratio_total_jaryo = rank_total.rank_ratio_jaryo
        score_student.rank_ratio_total_sanghwang = rank_total.rank_ratio_sanghwang
        score_student.rank_ratio_total_psat = rank_total.rank_ratio_psat

        score_student.rank_department_heonbeob = rank_department.rank_heonbeob
        score_student.rank_department_eoneo = rank_department.rank_eoneo
        score_student.rank_department_jaryo = rank_department.rank_jaryo
        score_student.rank_department_sanghwang = rank_department.rank_sanghwang
        score_student.rank_department_psat = rank_department.rank_psat

        score_student.rank_ratio_department_heonbeob = rank_department.rank_ratio_heonbeob
        score_student.rank_ratio_department_eoneo = rank_department.rank_ratio_eoneo
        score_student.rank_ratio_department_jaryo = rank_department.rank_ratio_jaryo
        score_student.rank_ratio_department_sanghwang = rank_department.rank_ratio_sanghwang
        score_student.rank_ratio_department_psat = rank_department.rank_ratio_psat

        score_student.save()
        return score_student


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
                    'number': number,
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
        self.is_confirmed = self.set_is_confirmed()
        self.next_url = self.get_next_url()

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
                answer_predict = self.get_answer_predict()
                self.update_score_student_virtual(answer_student, answer_predict)
            return True
        except self.answer_model.DoesNotExist:
            pass

    def get_next_url(self):
        answer_sub_list = (
            self.answer_model.objects
            .filter(student=self.student, is_confirmed=True)
            .distinct().values_list('sub', flat=True)
        )
        for sub in self.sub_dict.keys():
            if sub not in answer_sub_list:
                return reverse_lazy('predict:answer_input', args=[sub])
        return reverse_lazy('predict:index')

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

    def get_answer_predict(self) -> dict:
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
            number = prob['number']
            answer_count_list = []  # list for counting answers
            for i in range(5):
                ans_number = i + 1
                answer_count_list.append(prob[f'count_{ans_number}'])
            answer_predict_number = answer_count_list.index(max(answer_count_list)) + 1
            answer_predict[sub].append(
                {
                    'number': number,
                    'ans_number': answer_predict_number,
                }
            )
        return answer_predict

    def update_score_student_virtual(self, answer_student, answer_predict):
        field = self.sub_field[self.sub]
        answer_predict_sub = answer_predict[self.sub]

        problem_count = self.problem_count_dict[self.sub]
        correct_count = 0
        score_student_virtual, _ = self.statistics_virtual_model.objects.get_or_create(student=self.student)

        for i in range(problem_count):
            number = i + 1
            if getattr(answer_student, f'prob{number}') == answer_predict_sub[i]['ans_number']:
                correct_count += 1
        score = 100 * correct_count / problem_count
        setattr(score_student_virtual, field, score)

        score_eoneo = score_student_virtual.score_eoneo or 0
        score_jaryo = score_student_virtual.score_jaryo or 0
        score_sanghwang = score_student_virtual.score_sanghwang or 0
        score_student_virtual.score_psat = score_eoneo + score_jaryo + score_sanghwang
        score_student_virtual.score_psat_avg = score_student_virtual.score_psat / 3
        score_student_virtual.save()
