from django.db import transaction
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from .base_mixins import BaseMixin
from ..utils import get_all_ranks_dict, get_all_score_stat_sub_dict


class IndexViewMixIn(ConstantIconSet, BaseMixin):
    sub_title: str  # 페이지 제목
    units: list  # 모집 단위
    departments: list | None  # 직렬

    all_answer_count: dict  # PredictAnswerCount data
    dataset_answer_student: list  # PredictAnswer data
    answer_student_status: dict  # 과목별 답안 제출 완료 여부
    participant_count: dict  # 과목별 총 참여자 수

    data_answer: dict  # data_answer_correct, data_answer_predict, data_answer_student
    info_answer_student: dict  # index_info_answer data
    all_score_stat: dict  # PredictStatistics data: 전체 및 직렬별 전체 통계 자료
    score_student: dict  # PredictStatistics data: 전체 및 직렬별 개인 통계 자료

    def get_properties(self):
        super().get_properties()

        self.sub_title = self.get_sub_title()
        self.units = self.unit_model.objects.filter(exam__abbr=self.ex)
        self.departments = self.get_departments()

        self.all_answer_count = self.get_all_answer_count()
        self.dataset_answer_student = self.get_dataset_answer_student()
        self.answer_student_status = self.get_answer_student_status()
        self.participant_count = self.get_participant_count()

        self.data_answer = self.get_data_answer()
        self.info_answer_student = self.get_info_answer_student()

        if self.current_time > self.answer_opened_at and self.student:
            statistics_student = self.calculate_score(self.answer_correct_dict, 'real')
            self.all_score_stat = get_all_score_stat_sub_dict(self.get_statistics_qs, self.student)
            self.score_student = self.get_score_student(statistics_student)
            self.update_info_answer_student()
        else:
            self.all_score_stat = {'전체': '', '직렬': ''}
            self.score_student = {}

    def get_sub_title(self) -> str:
        if self.category == 'PSAT':
            return f'{self.year}년 {self.exam_name} 합격 예측'
        elif self.category == 'Prime':
            return f'제{self.round}회 {self.exam_name} 성적 예측'

    def get_departments(self) -> list:
        return self.department_model.objects.filter(unit__exam__abbr=self.ex).values()

    def get_all_answer_count(self) -> dict:
        answer_count_dict = {'헌법': [], '언어': [], '자료': [], '상황': []}
        answer_count_list = (
            self.answer_count_model.objects.filter(
                category=self.category,
                year=self.year,
                ex=self.ex,
                round=self.round)
            .order_by('sub', 'number').values(
                'sub', 'number', 'answer',
                'count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5', 'count_total',
                'rate_0', 'rate_1', 'rate_2', 'rate_3', 'rate_4', 'rate_5',
            )
        )
        for prob in answer_count_list:
            sub = prob['sub']
            prob['rate_None'] = 0
            answer_count_dict[sub].append(prob)
        return answer_count_dict

    def get_dataset_answer_student(self) -> list:
        return self.answer_model.objects.defer('timestamp').filter(student=self.student).values()

    def get_answer_student_status(self):
        status = {'헌법': False, '언어': False, '자료': False, '상황': False, '피셋': False}
        for dataset in self.dataset_answer_student:
            sub = dataset['sub']
            status[sub] = dataset['is_confirmed']
        if all([status['언어'], status['자료'], status['상황']]):
            status['피셋'] = True
        return status

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
        target_answers = self.data_answer['answer_predict']
        score_virtual = self.calculate_score(target_answers, 'virtual')
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
                'sub_eng': self.sub_eng_dict[sub],
                'subject': self.subject_dict[sub],
                'participants': self.participant_count[sub],
                'problem_count': problem_count,
                'answer_count': answer_count,
                'score_virtual': score_virtual[sub],
                'score_real': None,
                'is_confirmed': is_confirmed,
            }
        info_answer_student['피셋'] = {
            'icon': '',
            'sub': '피셋',
            'sub_eng': 'psat',
            'subject': 'PSAT 평균',
            'participants': max(
                info_answer_student['헌법']['participants'],
                info_answer_student['언어']['participants'],
                info_answer_student['자료']['participants'],
                info_answer_student['상황']['participants'],
            ),
            'problem_count': sum(self.problem_count_dict.values()),
            'answer_count': sum([
                info_answer_student['헌법']['answer_count'],
                info_answer_student['언어']['answer_count'],
                info_answer_student['자료']['answer_count'],
                info_answer_student['상황']['answer_count'],
            ]),
            'score_virtual': round(sum([
                info_answer_student['언어']['score_virtual'],
                info_answer_student['자료']['score_virtual'],
                info_answer_student['상황']['score_virtual'],
            ]) / 3, 1),
            'score_real': 0,
            'is_confirmed': all([
                info_answer_student['헌법']['is_confirmed'],
                info_answer_student['언어']['is_confirmed'],
                info_answer_student['자료']['is_confirmed'],
                info_answer_student['상황']['is_confirmed'],
            ]),
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

        # data_answer_correct
        for sub, data in data_answer_correct.items():
            for index, prob in enumerate(data):
                rate_correct = 0
                ans_number_list = []
                ans_number_correct = prob['ans_number']

                problem_set = self.all_answer_count[sub]
                if problem_set:
                    problem = problem_set[index]  # 정답률 추출 타겟 문제
                    if ans_number_correct in range(1, 6):
                        rate_correct = problem[f'rate_{ans_number_correct}']
                    else:
                        ans_number_list = [int(digit) for digit in str(ans_number_correct)]
                        rate_correct = sum(problem[f'rate_{ans}'] for ans in ans_number_list)
                prob['ans_number_list'] = ans_number_list
                prob['rate_correct'] = rate_correct

        # data_answer_predict
        for sub, data in self.all_answer_count.items():
            for problem in data:
                number = problem['number']
                ans_number_correct = data_answer_correct[sub][number - 1]['ans_number']
                answer_count_list = []  # list for counting answers
                for i in range(5):
                    answer_count_list.append(problem[f'count_{i + 1}'])
                ans_number_predict = answer_count_list.index(max(answer_count_list)) + 1  # 예상 정답
                rate_accuracy = problem[f'rate_{ans_number_predict}']  # 정확도

                result = 'O'
                if ans_number_correct and ans_number_correct != ans_number_predict:
                    result = 'X'
                data_answer_predict[sub].append(
                    {
                        'number': number,
                        'ans_number': ans_number_predict,
                        'result': result,
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

                result = 'O'
                if self.current_time > self.answer_opened_at:
                    ans_number_correct = data_answer_correct[sub][i]['ans_number']
                    ans_number_list_correct = data_answer_correct[sub][i]['ans_number_list']
                    if ans_number_correct in range(1, 6):
                        if ans_number_student != ans_number_correct:
                            result = 'X'
                    else:
                        if ans_number_student not in ans_number_list_correct:
                            result = 'X'

                problem_set = self.all_answer_count[sub]
                rate_selection = 0
                if problem_set:
                    rate_selection = problem_set[i][f'rate_{ans_number_student}']
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

    def calculate_score(self, target_answers, score_type):
        model_dict = {
            'virtual': self.statistics_virtual_model,
            'real': self.statistics_model,
        }
        model = model_dict[score_type]

        score_dict = {'헌법': 0, '언어': 0, '자료': 0, '상황': 0}
        if self.ex == '칠급':
            score_dict.pop('헌법')

        for sub, data in self.data_answer['answer_student'].items():
            correct_count = 0
            for index, problem in enumerate(data):
                answer_correct = 0
                if target_answers[sub]:
                    answer_correct = target_answers[sub][index]['ans_number']
                answer_student = problem['ans_number']

                if answer_correct <= 5 and answer_correct == answer_student:
                    correct_count += 1
                if answer_correct > 5:
                    answer_correct_list = [int(digit) for digit in str(answer_correct)]
                    if answer_student in answer_correct_list:
                        correct_count += 1
            if data:
                score_dict[sub] = correct_count * 100 / len(data)

        score_dict['psat'] = sum([score_dict['언어'], score_dict['자료'], score_dict['상황']])
        score_dict['psat_avg'] = score_dict['psat'] / 3

        if self.student:
            with transaction.atomic():
                score_student, _ = model.objects.get_or_create(student=self.student)
                for sub, score in score_dict.items():
                    field = self.sub_field[sub]
                    setattr(score_student, field, score_dict[sub])
                score_student.save()

        if score_type == 'virtual':
            return score_dict
        elif score_type == 'real':
            return score_student

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

    def get_score_student(self, statistics_student):
        all_ranks = get_all_ranks_dict(self.get_statistics_qs, self.student.user_id)
        rank_total = all_ranks['전체']
        rank_department = all_ranks['직렬']

        sub_list = ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat']
        for sub in sub_list:
            rank_total_value = getattr(rank_total, f'rank_{sub}')
            rank_ratio_total_value = getattr(rank_total, f'rank_ratio_{sub}')
            rank_department_value = getattr(rank_department, f'rank_{sub}')
            rank_ratio_department_value = getattr(rank_department, f'rank_ratio_{sub}')

            setattr(statistics_student, f'rank_total_{sub}', rank_total_value)
            setattr(statistics_student, f'rank_ratio_total_{sub}', rank_ratio_total_value)
            setattr(statistics_student, f'rank_department_{sub}', rank_department_value)
            setattr(statistics_student, f'rank_ratio_department_{sub}', rank_ratio_department_value)
        statistics_student.save()

        score_student = {'헌법': {}, '언어': {}, '자료': {}, '상황': {}, '피셋': {}}
        if self.ex == '칠급':
            score_student.pop('헌법')

        for sub, data in score_student.items():
            data['sub'] = sub
            data['sub_eng'] = self.sub_eng_dict[sub]
            data['subject'] = self.subject_dict[sub]
            data['is_confirmed'] = self.answer_student_status[sub]
            data['icon'] = self.ICON_SUBJECT[sub]

            sub_eng = data['sub_eng']
            if sub_eng == 'psat':
                data['score'] = getattr(statistics_student, f'score_psat_avg')
            else:
                data['score'] = getattr(statistics_student, f'score_{sub_eng}')
            data['rank_total'] = getattr(statistics_student, f'rank_total_{sub_eng}')
            data['rank_ratio_total'] = getattr(statistics_student, f'rank_ratio_total_{sub_eng}')
            data['rank_department'] = getattr(statistics_student, f'rank_department_{sub_eng}')
            data['rank_ratio_department'] = getattr(statistics_student, f'rank_ratio_department_{sub_eng}')

        return score_student

    def update_info_answer_student(self):
        sub_field = {
            '헌법': 'score_heonbeob',
            '언어': 'score_eoneo',
            '자료': 'score_jaryo',
            '상황': 'score_sanghwang',
            '피셋': 'score_psat_avg',
        }
        for sub, field in sub_field.items():
            score_real = self.score_student[sub]['score']
            self.info_answer_student[sub]['score_real'] = round(score_real, 1)


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
        self.subject = self.subject_dict[self.sub]

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
        sub_dict = {
            '헌법': '헌법',
            '언어': '언어논리',
            '자료': '자료해석',
            '상황': '상황판단',
        }
        answer_sub_list = (
            self.answer_model.objects
            .filter(student=self.student, is_confirmed=True)
            .distinct().values_list('sub', flat=True)
        )
        for sub in sub_dict.keys():
            if sub not in answer_sub_list:
                return reverse_lazy('score_old:predict-answer-input', args=[sub])
        return reverse_lazy('score_old:predict-index')

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
