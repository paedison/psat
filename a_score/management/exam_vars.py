import dataclasses
import pandas as pd

from a_score.models import prime_psat_models, prime_police_models


@dataclasses.dataclass
class CommandScoreExamVars:
    exam_type: str
    exam_year: int
    exam_round: int
    file_name: str

    @property
    def is_police(self):
        return self.exam_type == 'police'

    @property
    def is_psat(self):
        return self.exam_type == 'psat'

    @property
    def exam_model(self):
        default = {
            'police': prime_police_models.PrimePoliceExam,
            'psat': prime_psat_models.PrimePsatExam,
        }
        return default[self.exam_type]

    @property
    def student_model(self):
        default = {
            'police': prime_police_models.PrimePoliceStudent,
            'psat': prime_psat_models.PrimePsatStudent,
        }
        return default[self.exam_type]

    @property
    def answer_count_model(self):
        default = {
            'police': prime_police_models.PrimePoliceAnswerCount,
            'psat': prime_psat_models.PrimePsatAnswerCount,
        }
        return default[self.exam_type]

    @property
    def exam_info(self):
        return {'year': self.exam_year, 'round': self.exam_round}

    @property
    def exam(self):
        return self.exam_model.objects.filter(**self.exam_info).first()

    @property
    def departments(self) -> list:
        default = {
            'police': ['일반', '세무회계', '사이버'],
            'psat': [
                '5급 일반행정', '5급 재경', '5급 기술', '5급 기타',
                '7급 행정', '7급 기술', '일반외교',
                '지역인재 7급 행정', '지역인재 7급 기술', '기타 직렬'
            ]
        }
        return default[self.exam_type]

    @property
    def subject_fields(self):
        default = {
            'police': ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob'],
            'psat': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang'],
        }
        return default[self.exam_type]

    @property
    def only_psat_fields(self):
        return ['eoneo', 'jaryo', 'sanghwang']

    @property
    def final_field(self):
        default = {'police': 'sum', 'psat': 'psat_avg'}
        return default[self.exam_type]

    def get_final_score(self, score):
        if self.is_police:
            return sum(s for s in score.values())
        if self.is_psat:
            sum_list = [score[fld] for fld in self.only_psat_fields if fld in score]
            return round(sum(sum_list) / 3, 1) if sum_list else 0

    @property
    def score_fields(self):
        default = {
            'police': ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe', 'minbeob', 'haenghag', 'haengbeob', 'sum'],
            'psat': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg'],
        }
        return default[self.exam_type]

    @property
    def common_subject_fields(self):
        if self.is_police:
            return ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']

    @property
    def subject_vars(self):
        default = {
            'police': {
                '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
                '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
                '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
                '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
            },
            'psat': {
                '헌법': ('헌법', 'heonbeob'), '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
                '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
            },
        }
        return default[self.exam_type]

    @property
    def subject_fields_dict(self):
        default = {
            'police': {
                '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
                '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
                '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
            },
            'psat': {
                '헌법': 'heonbeob', '언어논리': 'eoneo', '자료해석': 'jaryo', '상황판단': 'sanghwang',
            },
        }
        return default[self.exam_type]

    @property
    def count_fields(self):
        default = {
            'police': ['count_0', 'count_1', 'count_2', 'count_3', 'count_4'],
            'psat': ['count_0', 'count_1', 'count_2', 'count_3', 'count_4', 'count_5'],
        }
        return default[self.exam_type]

    @property
    def all_count_fields(self):
        return self.count_fields + ['count_multiple', 'count_total']

    def get_problem_count(self, field):
        if self.is_psat and field == 'heonbeob':
            return 25
        return 40

    @property
    def dict_score_unit(self):
        default = {
            'police': {
                'hyeongsa': 3, 'gyeongchal': 3,
                'sebeob': 2, 'hoegye': 2, 'jeongbo': 2, 'sine': 2,
                'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
            },
            'psat': {'heonbeob': 4, 'eoneo': 2.5, 'jaryo': 2.5, 'sanghwang': 2.5},
        }
        return default[self.exam_type]

    @property
    def rank_list(self): return ['all_rank', 'top_rank', 'mid_rank', 'low_rank']

    @property
    def answer_official(self) -> dict[str, list]:
        df = pd.read_excel(self.file_name, sheet_name='정답', header=0, index_col=0)
        df.fillna(value=0, inplace=True)
        answer_official = {}
        for subject, answers in df.items():
            field = self.subject_fields_dict[subject]
            answer_official[field] = [int(ans) for ans in answers if ans]
        return answer_official

    @property
    def qs_student(self):
        return self.student_model.objects.filter(**self.exam_info)

    def get_problem_info(self, field: str, number: int):
        return {
            'year': self.exam_year, 'round': self.exam_round,
            'subject': field, 'number': number,
        }


data1 = [
    {'type': 'input', 'field': 'heonbeob', 'sub': '헌법', 'subject': '헌법', 'answer': [], 'confirmed': False},
    {'type': 'input', 'field': 'eoneo', 'sub': '언어', 'subject': '언어논리', 'answer': [], 'confirmed': False},
    {'type': 'input', 'field': 'jaryo', 'sub': '자료', 'subject': '자료해석', 'answer': [], 'confirmed': False},
    {'type': 'input', 'field': 'sanghwang', 'sub': '상황', 'subject': '상황판단', 'answer': [], 'confirmed': False},
    {'type': 'final', 'field': 'psat_avg', 'sub': '평균', 'subject': 'PSAT 평균', 'confirmed': False},
]
data2 = {
    'heonbeob': {'answer': [], 'confirmed': False},
    'eoneo': {'answer': [], 'confirmed': False},
    'jaryo': {'answer': [], 'confirmed': False},
    'sanghwang': {'answer': [], 'confirmed': False},
}
data3 = [
    ['heonbeob', False, 0, []],
    ['eoneo', False, 0, []],
    ['jaryo', False, 0, []],
    ['sanghwang', False, 0, []],
    ['psat_avg', False, 0, []],
]
data4 = [
    ['heonbeob', [4, 4, 3, 1, 4, 1, 4, 4, 2, 2, 3, 1, 1, 3, 4, 2, 3, 2, 3, 4, 3, 2, 3, 2, 1], False, 0],
    ['eoneo', [3, 3, 3, 5, 1, 5, 3, 2, 2, 2, 3, 1, 2, 3, 3, 3, 5, 2, 2, 5, 5, 5, 5, 5, 4, 5, 4, 5, 1, 4, 2, 3, 4, 2, 3, 3, 4, 3, 5, 4], False, 0],
    ['jaryo', [2, 3, 2, 3, 3, 4, 4, 1, 4, 1, 1, 2, 1, 4, 4, 3, 2, 4, 1, 3, 5, 1, 4, 4, 1, 4, 5, 4, 2, 3, 4, 2, 5, 2, 5, 4, 1, 5, 5, 1], False, 0],
    ['sanghwang', [4, 3, 2, 1, 2, 5, 5, 4, 4, 5, 5, 1, 4, 2, 3, 5, 5, 1, 1, 2, 1, 2, 4, 1, 2, 3, 4, 2, 3, 4, 2, 1, 4, 3, 3, 4, 4, 5, 4, 2], False, 0],
    ['psat_avg', [], False, 0],
]
