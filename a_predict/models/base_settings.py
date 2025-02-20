from django.utils import timezone
from datetime import datetime

import pytz
from django.db import models

from common.models import User


class ChoiceMethod:
    @staticmethod
    def get_this_year() -> int: return datetime.now().year

    @staticmethod
    def get_next_year() -> int: return datetime.now().year + 1

    @staticmethod
    def year_choices() -> list:
        years = [(year, f'{year}년') for year in range(2024, datetime.now().year + 2)]
        years.reverse()
        return years

    @staticmethod
    def number_choices() -> list: return [(number, f'{number}번') for number in range(1, 41)]

    # PSAT exam, unit, subject choices
    @staticmethod
    def psat_exam_choices() -> dict:
        return {
            '행시': '5급공채/외교원/지역인재 7급',
            '입시': '입법고시',
            '칠급': '7급공채/민간경력 5·7급',
        }

    @staticmethod
    def psat_unit_choices() -> dict:
        return {
            '5급공채 등': {
                '5급 행정(전국)': '5급 행정(전국)',
                '5급 행정(지역)': '5급 행정(지역)',
                '5급 기술(전국)': '5급 기술(전국)',
                '5급 기술(지역)': '5급 기술(지역)',
                '외교관후보자': '외교관후보자',
                '지역인재 7급': '지역인재 7급',
            },
            '입법고시': '입법고시',
            '7급공채 등': {
                '7급 국가직(일반)': '7급 국가직(일반)',
                '7급 국가직(장애인)': '7급 국가직(장애인)',
                '민간경력': '민간경력',
            },
        }

    @staticmethod
    def psat_department_choices() -> dict:
        return {
            '5급 행정(전국)': {
                '5급 행정(전국)-일반행정': '일반행정',
                '5급 행정(전국)-인사조직': '인사조직',
                '5급 행정(전국)-법무행정': '법무행정',
                '5급 행정(전국)-재경': '재경',
                '5급 행정(전국)-국제통상': '국제통상',
                '5급 행정(전국)-교육행정': '교육행정',
                '5급 행정(전국)-사회복지': '사회복지',
                '5급 행정(전국)-교정': '교정',
                '5급 행정(전국)-보호': '보호',
                '5급 행정(전국)-검찰': '검찰',
                '5급 행정(전국)-출입국관리': '출입국관리',
            },
            '5급 행정(지역)': {
                '5급 행정(지역)-서울': '서울',
                '5급 행정(지역)-부산': '부산',
                '5급 행정(지역)-대구': '대구',
                '5급 행정(지역)-인천': '인천',
                '5급 행정(지역)-광주': '광주',
                '5급 행정(지역)-대전': '대전',
                '5급 행정(지역)-울산': '울산',
                '5급 행정(지역)-세종': '세종',
                '5급 행정(지역)-경기': '경기',
                '5급 행정(지역)-강원': '강원',
                '5급 행정(지역)-충북': '충북',
                '5급 행정(지역)-충남': '충남',
                '5급 행정(지역)-전북': '전북',
                '5급 행정(지역)-전남': '전남',
                '5급 행정(지역)-경북': '경북',
                '5급 행정(지역)-경남': '경남',
                '5급 행정(지역)-제주': '제주',
            },
            '5급 기술(전국)': {
                '5급 기술(전국)-일반기계': '일반기계',
                '5급 기술(전국)-전기': '전기',
                '5급 기술(전국)-화공': '화공',
                '5급 기술(전국)-일반농업': '일반농업',
                '5급 기술(전국)-산림자원': '산림자원',
                '5급 기술(전국)-일반수산': '일반수산',
                '5급 기술(전국)-일반환경': '일반환경',
                '5급 기술(전국)-기상': '기상',
                '5급 기술(전국)-일반토목': '일반토목',
                '5급 기술(전국)-건축': '건축',
                '5급 기술(전국)-시설조경': '시설조경',
                '5급 기술(전국)-방재안전': '방재안전',
                '5급 기술(전국)-전산개발': '전산개발',
                '5급 기술(전국)-데이터': '데이터',
                '5급 기술(전국)-정보보호': '정보보호',
                '5급 기술(전국)-통신기술': '통신기술',
            },
            '5급 기술(지역)': {
                '5급 기술(지역)-서울': '서울',
                '5급 기술(지역)-부산': '부산',
                '5급 기술(지역)-대구': '대구',
                '5급 기술(지역)-인천': '인천',
                '5급 기술(지역)-광주': '광주',
                '5급 기술(지역)-대전': '대전',
                '5급 기술(지역)-울산': '울산',
                '5급 기술(지역)-세종': '세종',
                '5급 기술(지역)-경기': '경기',
                '5급 기술(지역)-강원': '강원',
                '5급 기술(지역)-충북': '충북',
                '5급 기술(지역)-충남': '충남',
                '5급 기술(지역)-전북': '전북',
                '5급 기술(지역)-전남': '전남',
                '5급 기술(지역)-경북': '경북',
                '5급 기술(지역)-경남': '경남',
                '5급 기술(지역)-제주': '제주',
            },
            '외교관후보자': {'외교관후보자-일반외교': '일반외교'},
            '지역인재 7급': {
                '지역인재 7급-행정': '행정',
                '지역인재 7급-기술': '기술'
            },
            '입법고시': {
                '입법고시-일반행정': '일반행정',
                '입법고시-법제': '법제',
                '입법고시-재경': '재경',
                '입법고시-사서': '사서',
                '입법고시-전산': '전산',
            },
            '7급 국가직(일반)': {
                '7급 국가직(일반)-일반행정': '일반행정',
                '7급 국가직(일반)-우정사업본부': '우정사업본부',
                '7급 국가직(일반)-인사조직': '인사조직',
                '7급 국가직(일반)-재경': '재경',
                '7급 국가직(일반)-고용노동': '고용노동',
                '7급 국가직(일반)-교육행정': '교육행정',
                '7급 국가직(일반)-회계': '회계',
                '7급 국가직(일반)-선거행정': '선거행정',
                '7급 국가직(일반)-세무': '세무',
                '7급 국가직(일반)-관세': '관세',
                '7급 국가직(일반)-통계': '통계',
                '7급 국가직(일반)-감사': '감사',
                '7급 국가직(일반)-교정': '교정',
                '7급 국가직(일반)-보호': '보호',
                '7급 국가직(일반)-검찰': '검찰',
                '7급 국가직(일반)-출입국관리': '출입국관리',
                '7급 국가직(일반)-일반기계': '일반기계',
                '7급 국가직(일반)-전기': '전기',
                '7급 국가직(일반)-화공': '화공',
                '7급 국가직(일반)-일반농업': '일반농업',
                '7급 국가직(일반)-산림자원': '산림자원',
                '7급 국가직(일반)-일반토목': '일반토목',
                '7급 국가직(일반)-건축': '건축',
                '7급 국가직(일반)-방재안전': '방재안전',
                '7급 국가직(일반)-전산개발': '전산개발',
                '7급 국가직(일반)-데이터': '데이터',
                '7급 국가직(일반)-전송기술': '전송기술',
                '7급 국가직(일반)-외무영사': '외무영사',
            },
            '7급 국가직(장애인)': {
                '7급 국가직(장애인)-일반행정': '일반행정',
                '7급 국가직(장애인)-우정사업본부': '우정사업본부',
                '7급 국가직(장애인)-인사조직': '인사조직',
                '7급 국가직(장애인)-재경': '재경',
                '7급 국가직(장애인)-고용노동': '고용노동',
                '7급 국가직(장애인)-교육행정': '교육행정',
                '7급 국가직(장애인)-회계': '회계',
                '7급 국가직(장애인)-선거행정': '선거행정',
                '7급 국가직(장애인)-세무': '세무',
                '7급 국가직(장애인)-관세': '관세',
                '7급 국가직(장애인)-통계': '통계',
                '7급 국가직(장애인)-감사': '감사',
                '7급 국가직(장애인)-교정': '교정',
                '7급 국가직(장애인)-보호': '보호',
                '7급 국가직(장애인)-검찰': '검찰',
                '7급 국가직(장애인)-출입국관리': '출입국관리',
                '7급 국가직(장애인)-일반기계': '일반기계',
                '7급 국가직(장애인)-전기': '전기',
                '7급 국가직(장애인)-화공': '화공',
                '7급 국가직(장애인)-일반농업': '일반농업',
                '7급 국가직(장애인)-산림자원': '산림자원',
                '7급 국가직(장애인)-일반토목': '일반토목',
                '7급 국가직(장애인)-건축': '건축',
                '7급 국가직(장애인)-방재안전': '방재안전',
                '7급 국가직(장애인)-전산개발': '전산개발',
                '7급 국가직(장애인)-데이터': '데이터',
                '7급 국가직(장애인)-전송기술': '전송기술',
                '7급 국가직(장애인)-외무영사': '외무영사',
            },
            '민간경력': {
                '민간경력-5급': '5급',
                '민간경력-7급': '7급',
            },
        }

    @staticmethod
    def psat_subject_choices() -> dict:
        return {
            'heonbeob': '헌법',
            'eoneo': '언어논리',
            'jaryo': '자료해석',
            'sanghwang': '상황판단',
        }

    @staticmethod
    def psat_sub_choices() -> dict:
        return {
            'heonbeob': '헌법',
            'eoneo': '언어',
            'jaryo': '자료',
            'sanghwang': '상황',
        }

    @staticmethod
    def prime_psat_exam_choices() -> dict: return {'프모': '프라임 PSAT 전국모의고사'}

    @staticmethod
    def prime_psat_unit_choices() -> dict:
        return {
            '5급공채': '5급공채',
            '7급공채': '7급공채',
            '외교관후보자': '외교관후보자',
            '지역인재 7급': '지역인재 7급',
            '기타': '기타',
        }

    @staticmethod
    def prime_psat_department_choices() -> dict:
        return {
            '5급공채': {
                '5급 일반행정': '5급 일반행정',
                '5급 재경': '5급 재경',
                '5급 기술': '5급 기술',
                '5급 기타': '5급 기타'
            },
            '7급공채': {
                '7급 행정': '7급 행정',
                '7급 기술': '7급 기술'
            },
            '외교관후보자': {'일반외교': '일반외교'},
            '지역인재 7급': {
                '지역인재 7급 행정': '지역인재 7급 행정',
                '지역인재 7급 기술': '지역인재 7급 기술'
            },
            '기타': {'기타 직렬': '기타 직렬'},
        }

    # Police exam, unit, department, subject choices
    @staticmethod
    def police_exam_choices() -> dict: return {'경위': '경위공채'}

    @staticmethod
    def police_unit_choices() -> dict: return {'경위': '경위'}

    @staticmethod
    def police_department_choices() -> dict:
        return {
            '일반': '일반',
            '세무': '세무회계',
            '사이': '사이버',
        }

    @staticmethod
    def police_subject_choices() -> dict:
        return {
            'hyeongsa': '형사법', 'heonbeob': '헌법',  # 전체 공통
            'gyeongchal': '경찰학', 'beomjoe': '범죄학',  # 일반 필수
            'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙',  # 일반 선택
            'sebeob': '세법개론', 'hoegye': '회계학',  # 세무회계 필수
            'sangbeob': '상법총칙', 'gyeongje': '경제학', 'tonggye': '통계학', 'jaejeong': '재정학',  # 세무회계 선택
            'jeongbo': '정보보호론', 'sine': '시스템네트워크보안',  # 사이버 필수
            'debe': '데이터베이스론', 'tongsin': '통신이론', 'sowe': '소프트웨어공학',  # 사이버 선택
        }

    @staticmethod
    def police_sub_choices() -> dict:
        return {
            'hyeongsa': '형사', 'heonbeob': '헌법',  # 전체 공통
            'gyeongchal': '경찰', 'beomjoe': '범죄',  # 일반 필수
            'haengbeob': '행법', 'haenghag': '행학', 'minbeob': '민법',  # 일반 선택
            'sebeob': '세법', 'hoegye': '회계',  # 세무회계 필수
            'sangbeob': '상법', 'gyeongje': '경제', 'tonggye': '통계', 'jaejeong': '재정',  # 세무회계 선택
            'jeongbo': '정보', 'sine': '시네',  # 사이버 필수
            'debe': '데베', 'tongsin': '통신', 'sowe': '소웨',  # 사이버 선택
        }

    @staticmethod
    def prime_police_exam_choices() -> dict: return {'프모': '프라임 경위공채 전국모의고사'}

    @staticmethod
    def prime_police_department_choices() -> dict: return {'일반': '일반'}

    @staticmethod
    def prime_police_subject_choices() -> dict:
        return {
            'hyeongsa': '형사법', 'heonbeob': '헌법',  # 전체 공통
            'gyeongchal': '경찰학', 'beomjoe': '범죄학',  # 일반 필수
            'haengbeob': '행정법', 'haenghag': '행정학', 'minbeob': '민법총칙',  # 일반 선택
        }

    def get_subject_from_field(self, field) -> str:
        subject_dict = self.psat_subject_choices()
        subject_dict.update(self.police_subject_choices())
        try:
            return subject_dict[field]
        except KeyError:
            return ''

    def get_sub_from_field(self, field) -> str:
        sub_dict = self.psat_sub_choices()
        sub_dict.update(self.police_sub_choices())
        try:
            return sub_dict[field]
        except KeyError:
            return ''

    def get_field_from_subject(self, subject) -> str:
        subject_dict = self.psat_subject_choices()
        subject_dict.update(self.police_subject_choices())
        for field, s in subject_dict.items():
            if s == subject:
                return field

    def get_field_from_sub(self, sub) -> str:
        sub_dict = self.psat_sub_choices()
        sub_dict.update(self.police_sub_choices())
        for field, s in sub_dict.items():
            if s == sub:
                return field


class TimeRecordField(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성 일시')

    class Meta:
        abstract = True


class RemarksField(models.Model):
    remarks = models.TextField(null=True, blank=True, verbose_name='주석')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        message_type = kwargs.pop('message_type', '')
        if self.pk is not None and message_type:
            self.remarks = self.get_remarks(message_type)
        super().save(*args, **kwargs)

    def get_remarks(self, message_type: str) -> str:
        utc_now = datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M')
        remarks = self.remarks
        separator = '|' if remarks else ''
        if remarks:
            remarks += f'{separator}{message_type}_at:{utc_now}'
        else:
            remarks = f'{message_type}_at:{utc_now}'
        return remarks


class YearExamRoundField(models.Model):
    year = models.IntegerField()  # Should override when inherited
    exam = models.CharField(max_length=2, verbose_name='시험')  # Should override when inherited
    round = models.IntegerField(default=0, verbose_name='회차')  # round number for '프모'

    class Meta:
        abstract = True

    @property
    def exam_reference(self): return f'{self.year}{self.exam}{self.round}'


class Exam(YearExamRoundField):
    answer_official = models.JSONField(default=dict)

    page_opened_at = models.DateTimeField(default=timezone.now)
    exam_started_at = models.DateTimeField(default=timezone.now)
    exam_finished_at = models.DateTimeField(default=timezone.now)
    answer_predict_opened_at = models.DateTimeField(default=timezone.now)
    answer_official_opened_at = models.DateTimeField(default=timezone.now)
    participants = models.JSONField(default=dict, verbose_name='전체 참여자수')
    statistics = models.JSONField(default=dict, verbose_name='성적 통계')
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        unique_together = ['year', 'exam', 'round']
        ordering = ['year', 'exam', 'round']

    def __str__(self):
        return f'[Predict]{self.__class__.__name__}:{self.exam_reference}'

    @property
    def is_not_page_opened(self):
        return timezone.now() <= self.page_opened_at

    @property
    def is_not_finished(self):
        return timezone.now() <= self.exam_finished_at

    @property
    def is_collecting_answer(self):
        return self.exam_finished_at < timezone.now() <= self.answer_predict_opened_at

    @property
    def is_answer_predict_opened(self):
        return self.answer_predict_opened_at < timezone.now() <= self.answer_official_opened_at

    @property
    def is_answer_official_opened(self):
        return self.answer_official_opened_at <= timezone.now()

    @property
    def exam_abbr(self):
        exam_dict = {
            '행시': '5급공채 등',
            '입시': '입법고시',
            '칠급': '7급공채 등',
            '경위': '경위공채',
        }
        return exam_dict[self.exam]


class Unit(TimeRecordField, RemarksField):
    exam = models.CharField(max_length=2, verbose_name='시험')  # Should override when inherited
    name = models.CharField(max_length=20, verbose_name='모집단위')  # Should override when inherited
    order = models.IntegerField()

    class Meta:
        abstract = True
        unique_together = ['exam', 'name']
        ordering = ['order']

    def __str__(self): return f'[Predict]{self.__class__.__name__}:{self.exam}-{self.name}'


class Department(TimeRecordField, RemarksField):
    exam = models.CharField(max_length=2, verbose_name='시험')  # Should override when inherited
    unit = models.CharField(max_length=20, verbose_name='모집단위')  # Should override when inherited
    name = models.CharField(max_length=40, verbose_name='직렬')  # Should override when inherited
    order = models.IntegerField()

    class Meta:
        abstract = True
        unique_together = ['exam', 'unit', 'name']
        ordering = ['order']

    def __str__(self):
        return f'[Predict]{self.__class__.__name__}:{self.exam}-{self.unit}-{self.name}'


class Student(TimeRecordField, RemarksField, YearExamRoundField, ChoiceMethod):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Should override when inherited

    name = models.CharField(max_length=20, verbose_name='이름')
    serial = models.CharField(max_length=10, verbose_name='수험번호')
    unit = models.CharField(max_length=10, verbose_name='모집단위')  # Should override when inherited
    department = models.CharField(max_length=20, verbose_name='직렬')  # Should override when inherited

    password = models.CharField(max_length=10, null=True, blank=True, verbose_name='비밀번호')
    prime_id = models.CharField(max_length=15, blank=True, null=True, verbose_name='프라임 ID')

    data = models.JSONField(default=list, verbose_name='답안 자료')
    answer = models.JSONField(default=dict, verbose_name='답안')
    answer_count = models.JSONField(default=dict, verbose_name='답안 개수')
    answer_confirmed = models.JSONField(default=dict, verbose_name='답안 확정')
    answer_all_confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='답안 전체 확정 일시')

    score = models.JSONField(default=dict, verbose_name='점수')
    rank = models.JSONField(default=dict, verbose_name='등수')

    class Meta:
        abstract = True
        unique_together = ['year', 'exam', 'round', 'serial']

    def __str__(self):
        return f'[Predict]{self.__class__.__name__}:{self.exam_reference}({self.student_info})'

    @property
    def student_info(self): return f'{self.serial}-{self.name}'

    @property
    def exam_abbr(self):
        exam_dict = {
            '행시': '5급공채 등',
            '입시': '입법고시',
            '칠급': '7급공채 등',
        }
        return exam_dict[self.exam]

    def get_answer_count(self, subject_field):
        answer_student = self.answer[subject_field]
        return len([ans for ans in answer_student if ans])

    def save(self, *args, **kwargs):
        for field, answer_student in self.answer.items():
            self.answer_count[field] = len([ans for ans in answer_student if ans])
        super().save(*args, **kwargs)


class AnswerCount(TimeRecordField, YearExamRoundField, ChoiceMethod):
    subject = models.CharField(max_length=20, verbose_name='과목')  # Should override when inherited
    number = models.IntegerField(choices=ChoiceMethod.number_choices, default=1, verbose_name="번호")
    answer = models.IntegerField(default=0, verbose_name='공식정답')

    count_1 = models.IntegerField(default=0, verbose_name='①')
    count_2 = models.IntegerField(default=0, verbose_name='②')
    count_3 = models.IntegerField(default=0, verbose_name='③')
    count_4 = models.IntegerField(default=0, verbose_name='④')
    count_5 = models.IntegerField(default=0, verbose_name='⑤')
    count_0 = models.IntegerField(default=0, verbose_name='미표기')
    count_multiple = models.IntegerField(default=0, verbose_name='중복표기')
    count_total = models.IntegerField(default=0, verbose_name='총계')
    all = models.JSONField(default=dict, verbose_name='전체')
    filtered = models.JSONField(default=dict, verbose_name='필터링')

    class Meta:
        abstract = True
        unique_together = ['year', 'exam', 'round', 'subject', 'number']

    def __str__(self):
        return f'[Predict]{self.__class__.__name__}:{self.exam_reference}-{self.subject}{self.number:02}'

    def get_rate(self, answer: int | str) -> float:
        count = getattr(self, f'count_{answer}', 0)
        rate = count / self.count_total * 100 if self.count_total else 0
        return rate

    @property
    def rate_1(self): return self.get_rate(1)

    @property
    def rate_2(self): return self.get_rate(2)

    @property
    def rate_3(self): return self.get_rate(3)

    @property
    def rate_4(self): return self.get_rate(4)

    @property
    def rate_5(self): return self.get_rate(5)

    @property
    def rate_0(self): return self.get_rate(0)

    @property
    def rate_multiple(self): return self.get_rate('multiple')


class Location(TimeRecordField, YearExamRoundField, ChoiceMethod):
    serial_start = models.IntegerField(verbose_name='시작 수험번호')
    serial_end = models.IntegerField(verbose_name='마지막 수험번호')
    region = models.CharField(max_length=10, verbose_name='지역')
    department = models.CharField(max_length=128, verbose_name='직렬')
    school = models.CharField(max_length=30, verbose_name='학교명')
    address = models.CharField(max_length=50, verbose_name='주소')
    contact = models.CharField(max_length=20, blank=True, null=True, verbose_name='연락처')

    def __str__(self):
        return f'[Predict]{self.__class__.__name__}:{self.exam_reference}-{self.region}-{self.department}-{self.school}'

    class Meta:
        abstract = True
        unique_together = ['year', 'exam', 'round', 'serial_start', 'serial_end']
