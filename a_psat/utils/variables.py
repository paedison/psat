import datetime
from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from a_psat import filters, models
from common.utils import HtmxHttpRequest


@dataclass(kw_only=True)
class RequestContext:
    _request: HtmxHttpRequest

    def __post_init__(self):
        self.view_type = self._request.headers.get('View-Type', '')
        self.exam_year = self._request.GET.get('year', '')
        self.exam_exam = self._request.GET.get('exam', '')
        self.exam_subject = self._request.GET.get('subject', '')
        self.page_number = self._request.GET.get('page', 1)
        self.keyword = self._request.POST.get('keyword', '') or self._request.GET.get('keyword', '')
        self.student_name = self._request.GET.get('student_name', '')

    def get_filterset(self):
        problem_filter = filters.ProblemFilter if self._request.user.is_authenticated else filters.AnonymousProblemFilter
        return problem_filter(data=self._request.GET, request=self._request)

    def get_sub_title(self, end_string='기출문제') -> str:
        year = self.exam_year
        exam = self.exam_exam
        subject = self.exam_subject
        title_parts = []
        if year:
            title_parts.append(f'{year}년')
            if isinstance(year, str):
                year = int(year)

        if exam:
            exam_dict = {
                '행시': '5급공채/행정고시', '외시': '외교원/외무고시', '칠급': '7급공채',
                '입시': '입법고시', '칠예': '7급공채 예시', '민경': '민간경력', '견습': '견습',
            }
            if not year:
                exam_name = exam_dict[exam]
            else:
                if exam == '행시':
                    exam_name = '행정고시' if year < 2011 else '5급공채'
                elif exam == '외시':
                    exam_name = '외교원' if year == 2013 else '외무고시'
                elif exam == '칠급':
                    exam_name = '7급공채 모의고사' if year == 2020 else '7급공채'
                else:
                    exam_name = exam_dict[exam]
            title_parts.append(exam_name)

        if subject:
            subject_dict = {'헌법': '헌법', '언어': '언어논리', '자료': '자료해석', '상황': '상황판단'}
            title_parts.append(subject_dict[subject])

        if not year and not exam and not subject:
            title_parts.append('전체')
        else:
            title_parts.append('전체')
        sub_title = f'{" ".join(title_parts)} {end_string}'
        return sub_title


@dataclass(kw_only=True)
class ModelData:
    def __post_init__(self):
        self.psat = models.Psat
        self.problem = models.Problem

        self.predict_psat = models.PredictPsat
        self.category = models.PredictCategory
        self.statistics = models.PredictStatistics
        self.student = models.PredictStudent
        self.answer = models.PredictAnswer
        self.score = models.PredictScore

        self.rank_total = models.PredictRankTotal
        self.rank_category = models.PredictRankCategory
        self.rank_model_set = {'total': self.rank_total, 'category': self.rank_category}

        self.ac_all = models.PredictAnswerCount
        self.ac_top = models.PredictAnswerCountTopRank
        self.ac_mid = models.PredictAnswerCountMidRank
        self.ac_low = models.PredictAnswerCountLowRank
        self.ac_model_set = {'all': self.ac_all, 'top': self.ac_top, 'mid': self.ac_mid, 'low': self.ac_low}


@dataclass(kw_only=True)
class OfficialModelData:
    def __post_init__(self):
        self.psat = models.Psat
        self.problem = models.Problem

        self.tag = models.ProblemTag
        self.tagged = models.ProblemTaggedItem
        self.open = models.ProblemOpen
        self.like = models.ProblemLike
        self.rate = models.ProblemRate
        self.solve = models.ProblemSolve
        self.memo = models.ProblemMemo
        self.collection = models.ProblemCollection
        self.collection_item = models.ProblemCollectionItem
        self.annotation = models.ProblemAnnotation
        self.comment = models.ProblemComment
        self.comment_like = models.ProblemCommentLike


@dataclass(kw_only=True)
class PsatContext:
    _psat: models.Psat

    def is_not_for_predict(self):
        return any([
            not self._psat,
            not hasattr(self._psat, 'predict_psat'),
            not self._psat.predict_psat.is_active if hasattr(self._psat, 'predict_psat') else True,
        ])

    def before_exam_start(self):
        return timezone.now() < self._psat.predict_psat.exam_started_at

    def get_time_schedule(self) -> dict:
        if hasattr(self._psat, 'predict_psat'):
            predict_psat = self._psat.predict_psat
            start_time = predict_psat.exam_started_at
            finish_time = predict_psat.exam_finished_at

            if self._psat.exam in ['칠급', '칠예', '민경']:
                return {
                    '언어': (start_time, start_time + datetime.timedelta(minutes=120)),
                    '상황': (start_time, start_time + datetime.timedelta(minutes=120)),
                    '자료': (start_time + datetime.timedelta(minutes=180), finish_time),
                    '평균': (start_time, finish_time),
                }
            else:
                return {
                    '헌법': (start_time, start_time + timedelta(minutes=115)),
                    '언어': (start_time, start_time + timedelta(minutes=115)),
                    '자료': (start_time + timedelta(minutes=225), start_time + timedelta(minutes=315)),
                    '상황': (start_time + timedelta(minutes=360), finish_time),
                    '평균': (start_time, finish_time),
                }
        return {}


@dataclass(kw_only=True)
class SubjectVariants:
    _psat: models.Psat

    def __post_init__(self):
        # 외부 호출 변수 정의
        self.subject_vars, self.subject_vars_avg, self.subject_vars_avg_first, self.subject_vars_dict =\
            self.get_vars_all()

        self.sub_list, self.subject_list, self.subject_fields = self.get_all_list(self.subject_vars)
        self.sub_list_avg, self.subject_list_avg, self.subject_fields_avg = self.get_all_list(self.subject_vars_avg)
        self.sub_list_avg_first, self.subject_list_avg_first, self.subject_fields_avg_first = self.get_all_list(
            self.subject_vars_avg_first)

    def get_vars_all(self):
        if self._psat.exam in ['칠급', '칠예', '민경']:
            avg_vars = {'평균': ('PSAT 평균', 'average', 4, 75)}
            subject_vars = {
                '언어': ('언어논리', 'subject_1', 1, 25),
                '자료': ('자료해석', 'subject_2', 2, 25),
                '상황': ('상황판단', 'subject_3', 3, 25),
            }
        else:
            avg_vars = {'평균': ('PSAT 평균', 'average', 4, 145)}
            subject_vars = {
                '헌법': ('헌법', 'subject_0', 0, 25),
                '언어': ('언어논리', 'subject_1', 1, 40),
                '자료': ('자료해석', 'subject_2', 2, 40),
                '상황': ('상황판단', 'subject_3', 3, 40),
            }
        subject_vars_avg = dict(subject_vars, **avg_vars)
        subject_vars_avg_first = dict(avg_vars, **subject_vars)
        subject_vars_dict = {
            'base': subject_vars, 'avg_last': subject_vars_avg, 'avg_first': subject_vars_avg_first
        }
        return subject_vars, subject_vars_avg, subject_vars_avg_first, subject_vars_dict

    @staticmethod
    def get_all_list(_vars: dict):
        sub = list(_vars.keys())
        tuple_lists = list(zip(*_vars.values()))
        subject = tuple_lists[0]
        field = tuple_lists[1]
        return sub, subject, field

    def get_subject_variable(self, subject_field) -> tuple[str, str, int, int]:
        for sub, (subject, fld, field_idx, problem_count) in self.subject_vars.items():
            if subject_field == fld:
                return sub, subject, field_idx, problem_count


def get_prev_next_obj(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_obj = next_obj = None
    last_id = len(custom_list) - 1
    try:
        q = custom_list.index(pk)
        if q != 0:
            prev_obj = custom_data[q - 1]
        if q != last_id:
            next_obj = custom_data[q + 1]
        return prev_obj, next_obj
    except ValueError:
        return None, None
