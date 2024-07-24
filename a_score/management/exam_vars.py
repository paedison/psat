import dataclasses
import pandas as pd
from django.db.models import QuerySet

import a_score.models as models


@dataclasses.dataclass
class CommandScoreExamVars:
    exam_type: str
    exam_year: int
    exam_round: int
    file_name: str

    default_count_fields = ['count_0', 'count_1', 'count_2', 'count_3', 'count_4']
    extra_count_fields = ['count_multiple', 'count_total']
    rank_list = ['all_rank', 'top_rank', 'mid_rank', 'low_rank']
    subject_to_field_dict = {
        '언어논리': 'eoneo', '자료해석': 'jaryo', '상황판단': 'sanghwang',
        '형사법': 'hyeongsa', '헌법': 'heonbeob',  # 전체 공통
        '경찰학': 'gyeongchal', '범죄학': 'beomjoe',  # 일반 필수
        '행정법': 'haengbeob', '행정학': 'haenghag', '민법총칙': 'minbeob',  # 일반 선택
    }
    field_to_subject_dict = {
        'eoneo': '언어논리', 'jaryo': '자료해석', 'sanghwang': '상황판단',
        'hyeongsa': '형사법', 'heonbeob': '헌법',  # 전체 공통
        'gyeongchal': '경찰학', 'beomjoe': '범죄학',  # 일반 필수
        'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙',  # 일반 선택
    }
    subject_vars = {
        '언어': ('언어논리', 'eoneo'), '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'), '평균': ('PSAT 평균', 'psat_avg'),
        '형사': ('형사학', 'hyeongsa'), '헌법': ('헌법', 'heonbeob'),
        '경찰': ('경찰학', 'gyeongchal'), '범죄': ('범죄학', 'beomjoe'),
        '민법': ('민법총칙', 'minbeob'), '행학': ('행정학', 'haenghag'),
        '행법': ('행정법', 'haengbeob'), '총점': ('총점', 'sum'),
    }

    # psat vars
    psat_exam_model = models.PrimePsatExam
    psat_student_model = models.PrimePsatStudent
    psat_answer_count_model = models.PrimePsatAnswerCount
    psat_all_departments = [
        '5급 일반행정', '5급 재경', '5급 기술', '5급 기타', '일반외교',
        '7급 행정', '7급 기술', '지역인재 7급 행정', '지역인재 7급 기술', '기타 직렬'
    ]

    only_psat_fields = ['eoneo', 'jaryo', 'sanghwang']
    psat_all_answer_fields = ['heonbeob'] + only_psat_fields
    psat_final_field = 'psat_avg'
    psat_all_score_fields = psat_all_answer_fields + [psat_final_field]

    psat_count_fields = default_count_fields + ['count_5']
    psat_all_count_fields = psat_count_fields + extra_count_fields
    psat_score_unit = {'heonbeob': 4, 'eoneo': 2.5, 'jaryo': 2.5, 'sanghwang': 2.5}

    # police vars
    police_exam_model = models.PrimePoliceExam
    police_student_model = models.PrimePoliceStudent
    police_answer_count_model = models.PrimePoliceAnswerCount
    police_all_departments = ['일반', '세무회계', '사이버']

    police_common_subject_fields = ['hyeongsa', 'heonbeob', 'gyeongchal', 'beomjoe']
    police_selection_subject_fields = ['minbeob', 'haenghag', 'haengbeob']
    police_all_answer_fields = police_common_subject_fields + police_selection_subject_fields
    police_final_field = 'sum'
    police_all_score_fields = police_all_answer_fields + [police_final_field]

    police_count_fields = default_count_fields
    police_all_count_fields = police_count_fields + extra_count_fields
    police_score_unit = {
        'hyeongsa': 3, 'gyeongchal': 3, 'sebeob': 2, 'hoegye': 2, 'jeongbo': 2,
        'sine': 2, 'haengbeob': 1, 'haenghag': 1, 'minbeob': 1,
    }

    @property
    def is_police(self) -> bool:
        return self.exam_type == 'police'

    @property
    def is_psat(self) -> bool:
        return self.exam_type == 'psat'

    @property
    def exam_model(self) -> models.PrimePsatExam | models.PrimePoliceExam:
        return getattr(self, f'{self.exam_type}_exam_model')

    @property
    def student_model(self) -> models.PrimePsatStudent | models.PrimePoliceStudent:
        return getattr(self, f'{self.exam_type}_student_model')

    @property
    def answer_count_model(self)-> models.PrimePsatAnswerCount | models.PrimePoliceAnswerCount:
        return getattr(self, f'{self.exam_type}_answer_count_model')

    @property
    def exam_info(self) -> dict:
        return {'year': self.exam_year, 'round': self.exam_round}

    @property
    def exam(self) -> models.PrimePsatExam | models.PrimePoliceExam:
        return self.exam_model.objects.filter(**self.exam_info).first()

    @property
    def qs_student(self) -> QuerySet:
        return self.student_model.objects.filter(**self.exam_info)

    @property
    def all_departments(self) -> list:
        return getattr(self, f'{self.exam_type}_all_departments')

    @property
    def all_answer_fields(self) -> list:
        return getattr(self, f'{self.exam_type}_all_answer_fields')

    @property
    def final_field(self) -> str:
        return getattr(self, f'{self.exam_type}_final_field')

    @property
    def all_score_fields(self) -> list:
        return getattr(self, f'{self.exam_type}_all_score_fields')

    @property
    def all_count_fields(self) -> list:
        return getattr(self, f'{self.exam_type}_all_count_fields')

    def get_problem_info(self, field: str, number: int) -> dict:
        return dict(self.exam_info, **{'subject': field, 'number': number})

    def get_police_student_score_fields(self, selection) -> list:
            return self.police_common_subject_fields + [selection] + [self.police_final_field]

    def get_problem_count(self, field) -> int:
        return 25 if self.is_psat and field == 'heonbeob' else 40

    def get_score_unit(self, field) -> float | int:
        return getattr(self, f'{self.exam_type}_score_unit').get(field, 1.5)

    def get_answer_official(self) -> dict[str, list]:
        df = pd.read_excel(self.file_name, sheet_name='정답', header=0, index_col=0)
        df.fillna(value=0, inplace=True)
        answer_official = {}
        for subject, answers in df.items():
            field = self.get_field_name(subject)
            answer_official[field] = [int(ans) for ans in answers if ans]
        return answer_official

    def get_field_name(self, subject) -> str:
        return self.subject_to_field_dict[subject]

    def get_subject_name(self, field) -> str:
        return self.field_to_subject_dict[field]
