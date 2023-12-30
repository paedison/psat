from django.db.models import F

from reference import models as reference_models
from score import forms as score_forms
from score import models as score_models


def get_option(target) -> list[tuple]:
    target_option = []
    for t in target:
        if t not in target_option:
            target_option.append(t)
    return target_option


class ScoreExamList:
    exam_list = [
        {'year': 2023, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2023, 'ex': '칠급', 'exam': '7급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2023, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2022, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2022, 'ex': '칠급', 'exam': '7급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2022, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2021, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2021, 'ex': '칠급', 'exam': '7급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2021, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2021, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2020, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2020, 'ex': '칠급', 'exam': '7급공채(모)', 'sub': ['언어', '자료', '상황']},
        {'year': 2020, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2020, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2019, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2019, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2019, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2018, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2018, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2018, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2017, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2017, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2017, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황', '헌법']},
        {'year': 2016, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2016, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2016, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2015, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2015, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2015, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2014, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2014, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2014, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '외시', 'exam': '외교원', 'sub': ['언어', '자료', '상황']},
        {'year': 2013, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2012, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2012, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2012, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2011, 'ex': '행시', 'exam': '5급공채', 'sub': ['언어', '자료', '상황']},
        {'year': 2011, 'ex': '민경', 'exam': '민간경력', 'sub': ['언어', '자료', '상황']},
        {'year': 2011, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2010, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2010, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2009, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2009, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2008, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2008, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2007, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2007, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2006, 'ex': '행시', 'exam': '행정고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2006, 'ex': '견습', 'exam': '견습', 'sub': ['언어', '자료', '상황']},
        {'year': 2006, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료', '상황']},
        {'year': 2005, 'ex': '견습', 'exam': '견습', 'sub': ['언어', '자료', '상황']},
        {'year': 2005, 'ex': '외시', 'exam': '외무고시', 'sub': ['언어', '자료']},
        {'year': 2005, 'ex': '입시', 'exam': '입법고시', 'sub': ['언어', '자료']},
        {'year': 2004, 'ex': '외시', 'exam': '외무고시', 'sub': ['언어', '자료']}
    ]


class BaseMixin(ScoreExamList):
    psat_model = reference_models.Psat
    exam_model = reference_models.Exam
    problem_model = reference_models.PsatProblem
    subject_model = reference_models.Subject

    unit_model = score_models.PsatUnit
    department_model = score_models.PsatUnitDepartment
    student_model = score_models.PsatStudent
    temporary_model = score_models.PsatAnswerTemporary
    confirmed_model = score_models.PsatAnswerConfirmed
    # temporary_model = score_models.PsatTemporaryAnswer
    # confirmed_model = score_models.PsatConfirmedAnswer
    answer_count_model = score_models.PsatAnswerCount

    student_form = score_forms.PsatStudentForm

    request: any
    kwargs: dict

    user_id: int | None
    year: int
    ex: str
    exam: any

    option_year: list
    option_ex: list

    info: dict

    def get_properties(self):
        self.user_id: int | None = self.request.user.id if self.request.user.is_authenticated else None

        self.year: str = self.get_kwargs('year')
        self.ex: str = self.get_kwargs('ex')

        if self.year and self.ex:
            self.exam = self.get_exam()
            self.option_year = self.get_year_option()
            self.option_ex = self.get_ex_option()

        self.info = {
            'menu': 'score',
            'view_type': 'psatScore',
        }

    def get_kwargs(self, kw: str, default=''):
        return self.kwargs.get(kw, default)

    def get_exam(self):
        if self.year == '2020' and self.ex == '칠급':
            return self.exam_model.objects.get(name='7급공채 모의고사')
        else:
            return self.exam_model.objects.get(
                psat_exams__year=self.year, abbr=self.ex, psat_exams__subject__abbr='언어')

    def get_year_option(self) -> list[tuple]:
        year_list = (
            self.psat_model.objects.distinct()
            .values_list('year', flat=True).order_by('-year')
        )
        return get_option(year_list)

    def get_ex_option(self) -> list[tuple]:
        ex_list = (
            self.psat_model.objects.filter(year=self.year).distinct()
            .values(ex=F('exam__abbr'), exam_name=F('exam__name')).order_by('exam_id')
        )
        return get_option(ex_list)
