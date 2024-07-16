import os

from django.conf import settings
from django.db import transaction
from django.db.models import Count, QuerySet, F
from django.urls import reverse_lazy

from a_predict.models import (
    PsatExam, PsatUnit, PsatDepartment, PsatLocation,
    PsatStudent, PsatSubmittedAnswer, PsatAnswerCount,
)
from common.constants import icon_set_new
from common.utils import detect_encoding, HtmxHttpRequest


class ExamInfo:
    # Target PsatExam
    YEAR = 2024
    EXAM = '행시'
    ROUND = 0

    # Subject full name, field
    HEONBEOB = ('헌법', 'heonbeob')
    EONEO = ('언어논리', 'eoneo')
    JARYO = ('자료해석', 'jaryo')
    SANGHWANG = ('상황판단', 'sanghwang')
    PSAT_TOTAL = ('PSAT 총점', 'psat')
    PSAT_AVG = ('PSAT 평균', 'psat_avg')

    # Subject variables dictionary
    SUBJECT_VARS = {
        '헌법': HEONBEOB,
        '언어': EONEO,
        '자료': JARYO,
        '상황': SANGHWANG,
        '총점': PSAT_TOTAL,
        '평균': PSAT_AVG,
    }
    FIELD_VARS = {
        'heonbeob': ('헌법', '헌법'),
        'eoneo': ('언어', '언어논리'),
        'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'),
        'psat_total': ('총점', 'PSAT 총점'),
        'psat_avg': ('평균', 'PSAT 평균'),
    }

    # Customize PROBLEM_COUNT, SUBJECT_VARS by PsatExam
    if EXAM == '칠급':
        PROBLEM_COUNT = {'eoneo': 25, 'jaryo': 25, 'sanghwang': 25}
        SUBJECT_VARS.pop('헌법')
    else:
        PROBLEM_COUNT = {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40}

    # Answer file
    ANSWER_FILE = settings.BASE_DIR / 'a_predict/data/answers.csv'
    EMPTY_FILE = settings.BASE_DIR / 'a_predict/data/answers_empty.csv'
    ANSWER_FILE = ANSWER_FILE if os.path.exists(ANSWER_FILE) else EMPTY_FILE
    ANSWER_FILE_ENCODING = detect_encoding(ANSWER_FILE)

    # View info
    INFO = {
        'menu': 'predict',
        'view_type': 'predict',
    }

    # Queryset variables
    qs_exam = PsatExam.objects.filter(exam=EXAM, round=ROUND)
    qs_unit = PsatUnit.objects.filter(exam=EXAM)
    qs_department = PsatDepartment.objects.filter(exam=EXAM)
    qs_location = PsatLocation.objects.filter(year=YEAR, exam=EXAM)
    qs_student = PsatStudent.objects.filter(year=YEAR, exam=EXAM, round=ROUND)
    qs_student_answer = PsatStudent.objects.filter(
        year=YEAR, exam=EXAM, round=ROUND)
    qs_submitted_answer = PsatSubmittedAnswer.objects.filter(
        student__year=YEAR, student__exam=EXAM, student__round=ROUND)
    qs_answer_count = PsatAnswerCount.objects.filter(
        year=YEAR, exam=EXAM, round=ROUND).annotate(no=F('number')).order_by('subject', 'number')
    qs_official_answer = PsatExam.objects.filter(year=YEAR, exam=EXAM, round=ROUND)

    def create_student(self, student: PsatStudent, request: HtmxHttpRequest) -> PsatStudent:
        with transaction.atomic():
            student.year = self.YEAR
            student.exam = self.EXAM
            student.round = self.ROUND
            student.user = request.user
            student.save()
            PsatStudent.objects.get_or_create(student=student)
            return student

    def get_obj_student(self, request: HtmxHttpRequest) -> PsatStudent:
        return self.qs_student.filter(user=request.user).first()

    def get_obj_student_answer(self, request: HtmxHttpRequest) -> PsatStudent:
        return self.qs_student_answer.filter(student__user=request.user).first()

    def get_dict_participants_count(self) -> dict:
        qs_participants_count = self.qs_submitted_answer.values('subject').annotate(
            count=Count('student', distinct=True))
        return {self.SUBJECT_VARS[p['subject']][1]: p['count'] for p in qs_participants_count}

    def get_dict_data_answer_rate(self, data_answer_official: dict, qs_answer_count) -> dict:
        dict_answer_count = {field: [] for field in self.PROBLEM_COUNT.keys()}

        qs: PsatAnswerCount
        for qs in qs_answer_count:
            field = self.SUBJECT_VARS[qs.subject][1]
            dict_answer_count[field].append(qs)
            if data_answer_official:
                answer_official = data_answer_official[field][qs.number - 1]
                ans_official = answer_official['ans']
                qs.rate_correct = getattr(qs, f'rate_{ans_official}')
                answer_official['rate_correct'] = getattr(qs, f'rate_{ans_official}')

        return dict_answer_count

    @staticmethod
    def get_list_answer_empty(problem_count: int) -> list:
        answer_empty = []
        for i in range(1, problem_count + 1):
            answer_empty.append({'no': i, 'ans': ''})
        return answer_empty

    def get_list_answer_temp(
            self,
            request: HtmxHttpRequest,
            sub: str,
            queryset: PsatSubmittedAnswer | None = None
    ) -> list:
        problem_count: int = self.PROBLEM_COUNT[sub]
        answer_temp: list = self.get_list_answer_empty(problem_count=problem_count)
        if queryset is None:
            queryset = self.qs_submitted_answer.filter(student__user=request.user)
        for qs in queryset:
            qs: PsatSubmittedAnswer
            if qs.subject == sub:
                answer_temp[qs.number - 1] = {'no': qs.number, 'ans': qs.answer}
        return answer_temp

    def get_tuple_data_answer_student(
            self, request: HtmxHttpRequest,
            data_answer_rate: dict | None,
    ) -> tuple[dict[str, list], dict[str, int], dict[str, bool]]:
        qs_answer_final: PsatStudent = self.get_obj_student_answer(request=request)
        qs_answer_temp: QuerySet[PsatSubmittedAnswer] = self.qs_submitted_answer.filter(student__user=request.user)

        data_answer_student: dict[str, list] = qs_answer_final.answer
        data_answer_count: dict[str, int] = qs_answer_final.answer_count
        data_answer_confirmed: dict[str, bool] = qs_answer_final.answer_confirmed

        for field, value in data_answer_student.items():
            for answer_student in value:
                number = answer_student['no']
                ans_number = answer_student['ans']
                answer_rate: PsatAnswerCount = data_answer_rate[field][number - 1]
                answer_student['rate_selection'] = getattr(answer_rate, f'rate_{ans_number}')

        return data_answer_student, data_answer_count, data_answer_confirmed

    def create_submitted_answer(self, request: HtmxHttpRequest, sub: str) -> PsatSubmittedAnswer:
        student = self.get_obj_student(request=request)
        number = request.POST.get('number')
        answer = request.POST.get('answer')
        with transaction.atomic():
            submitted_answer, _ = PsatSubmittedAnswer.objects.get_or_create(student=student, subject=sub, number=number)
            submitted_answer.answer = answer
            submitted_answer.save()
            submitted_answer.refresh_from_db()
            return submitted_answer

    def get_tuple_answer_string_confirm(self, request: HtmxHttpRequest, sub: str) -> tuple[str, bool]:
        answer_temp: list = self.get_list_answer_temp(request=request, sub=sub)
        is_confirmed = True

        answer_list: list[str] = []
        for answer in answer_temp:
            ans_number = answer['ans_number']
            if ans_number == '':
                is_confirmed = False
            else:
                answer_list.append(str(ans_number))
        answer_string = ','.join(answer_list) if is_confirmed else ''
        return answer_string, is_confirmed

    def get_str_next_url(self, student_answer: PsatStudent) -> str:
        for sub in self.PROBLEM_COUNT.keys():
            field = self.SUBJECT_VARS[sub][1]
            is_confirmed = getattr(student_answer, f'{field}_confirmed')
            if not is_confirmed:
                return reverse_lazy('predict:answer-input', args=[sub])
        return reverse_lazy('predict_test:index')

    def get_dict_data_answer_predict(self, qs_answer_count) -> dict:
        data_answer_predict = {subject: [] for subject in self.PROBLEM_COUNT.keys()}
        qs: PsatAnswerCount
        for qs in qs_answer_count:
            field = self.SUBJECT_VARS[qs.subject][1]
            count_list = [c for c in [qs.count_1, qs.count_2, qs.count_3, qs.count_4, qs.count_5]]
            qs.ans_predict = count_list.index(max(count_list)) + 1
            qs.rate_accuracy = getattr(qs, f'rate_{qs.ans_predict}')
            data_answer_predict[field].append(qs)
        return data_answer_predict

    #
    # def get_dict_data_answer_predict(self, data_answer_official: dict, qs_answer_count: PsatAnswerCount) -> dict:
    #     data_answer_predict = {}
    #     for qs in qs_answer_count:
    #         field = self.SUBJECT_VARS[qs.subject][1]
    #         problem_count = self.PROBLEM_COUNT[qs.subject]
    #         data_answer_predict[qs.subject] = self.get_list_answer_empty(problem_count=problem_count)
    #         for idx in range(problem_count):
    #             ans_official = data_answer_official[field][idx]['ans'] if data_answer_official else None
    #
    #             answer_count_list = []  # list for counting answers
    #             for i in range(1, 6):
    #                 answer_count_list.append(problem[f'count_{i}'])
    #             ans_predict = answer_count_list.index(max(answer_count_list)) + 1  # 예상 정답
    #             rate_accuracy = problem[f'rate_{ans_predict}']  # 정확도
    #
    #             result = 'O'
    #             if ans_official and ans_official != ans_predict:
    #                 result = 'X'
    #             data_answer_predict[sub].append(
    #                 {
    #                     'no': number,
    #                     'ans': ans_predict,
    #                     'result': result,
    #                     'rate_accuracy': rate_accuracy,
    #                 }
    #             )

    def get_dict_info_answer_student_empty(self, field):
        sub = self.FIELD_VARS[field][0]
        return {
            'icon': icon_set_new.ICON_SUBJECT[sub],
            'sub': sub,
            'subject': self.SUBJECT_VARS[sub][0],
            'field': self.SUBJECT_VARS[sub][1],
        }

    def get_dict_info_answer_student(
            self,
            data_answer_student: dict,
            data_answer_count: dict,
            data_answer_confirmed: dict,
            data_answer_official: dict,
            data_answer_predict: dict,
    ) -> dict:
        participants_count = self.get_dict_participants_count()
        info_answer_student = {}
        if data_answer_student:
            psat_score_real = psat_score_predict = 0
            psat_fields = ['eoneo', 'jaryo', 'sanghwang']

            for field, value in data_answer_student.items():
                problem_count = self.PROBLEM_COUNT[field]
                answer_count = data_answer_count[field]
                is_confirmed = data_answer_confirmed[field]

                try:
                    participants = participants_count[field]
                except KeyError:
                    participants = 0

                correct_real_count = correct_predict_count = 0
                for idx, answer_student in enumerate(value):
                    ans_student = answer_student['ans']
                    ans_official = data_answer_official[field][idx]['ans'] if data_answer_official else None
                    ans_predict = data_answer_predict[field][idx].ans_predict

                    try:
                        ans_official_list = data_answer_official[field][idx]['ans_list']
                    except (KeyError, TypeError):
                        ans_official_list = None

                    result_real = 'X'
                    if ans_official_list and ans_student in ans_official_list:
                        result_real = 'O'
                    if ans_student == ans_official:
                        result_real = 'O'
                    answer_student['result_real'] = result_real
                    correct_real_count += 1 if result_real == 'O' else 0

                    result_predict = 'X'
                    if ans_student == ans_predict:
                        result_predict = 'O'
                    answer_student['result_predict'] = result_predict
                    correct_predict_count += 1 if result_predict == 'O' else 0

                score_real = correct_real_count * 100 / problem_count
                psat_score_real += score_real if field in psat_fields else 0

                score_predict = correct_predict_count * 100 / problem_count
                psat_score_predict += score_predict if field in psat_fields else 0

                info_answer_student[field] = self.get_dict_info_answer_student_empty(field)
                info_answer_student[field].update({
                    'problem_count': problem_count,
                    'participants': participants,
                    'answer_count': answer_count,
                    'score_real': correct_real_count * 100 / problem_count,
                    'score_predict': score_predict,
                    'is_confirmed': is_confirmed,
                })

            info_answer_student['psat_avg'] = self.get_dict_info_answer_student_empty('psat_avg')
            info_answer_student['psat_avg'].update({
                'participants': participants_count[max(participants_count)],
                'problem_count': sum([val for val in self.PROBLEM_COUNT.values()]),
                'answer_count': sum([val for val in data_answer_count.values()]),
                'score_real': psat_score_real / 3,
                'score_predict': psat_score_predict / 3,
                'is_confirmed': all(data_answer_confirmed),
            })
        return info_answer_student

    def get_dict_stat_data(
            self,
            student: PsatStudent,
            statistics_type: str,
            exam: PsatExam | None = None,
    ):
        filter_exp = {
            'student__year': student.year,
            'student__exam': student.exam,
            'student__round': student.round,
        }
        if statistics_type == 'department':
            filter_exp['student__department'] = student.department
        if exam:
            filter_exp['student__student_answers__confirmed_at__lte'] = exam.answer_official_opened_at
        queryset = PsatStudent.objects.filter(**filter_exp).values('score')

        score = {}
        stat_data = {}
        fields = list(self.PROBLEM_COUNT.keys())
        fields.append('psat_avg')
        for field in fields:
            sub, subject = self.FIELD_VARS[field]
            if field == 'psat_avg':
                is_confirmed = all(student.student_answers.answer_confirmed.values())
            else:
                is_confirmed = student.student_answers.answer_confirmed[field]

            score[field] = []
            for qs in queryset:
                if field in qs['score'].keys():
                    score[field].append(qs['score'][field])

            participants = len(score[field])
            sorted_scores = sorted(score[field], reverse=True)

            rank = sorted_scores.index(student.statistics.score[field]) + 1
            top_10_threshold = max(1, int(participants * 0.1))
            top_20_threshold = max(1, int(participants * 0.2))

            stat_data[field] = {
                'field': field,
                'sub': sub,
                'subject': subject,
                'icon': icon_set_new.ICON_SUBJECT[sub],
                'is_confirmed': is_confirmed,
                'rank': rank,
                'score': student.statistics.score[field],
                'participants': participants,
                'max_score': sorted_scores[0],
                'top_score_10': sorted_scores[top_10_threshold - 1],
                'top_score_20': sorted_scores[top_20_threshold - 1],
                'avg_score': sum(score[field]) / participants,
            }
        return stat_data
