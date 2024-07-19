from django.db import models

from .base_settings import Exam, Unit, Department, Student, AnswerCount, ChoiceMethod


class PoliceExam(Exam):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_next_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.police_exam_choices, default='경위', verbose_name='시험')

    class Meta:
        verbose_name = verbose_name_plural = "경위공채 성적예측 [1] 시험"
        db_table = 'a_predict_police_exam'


class PoliceUnit(Unit):
    # Override parent abstract model fields
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.police_exam_choices, default='경위', verbose_name='시험')
    name = models.CharField(
        max_length=20, choices=ChoiceMethod.police_unit_choices,
        default='경위', verbose_name='모집단위')

    class Meta:
        verbose_name = verbose_name_plural = "경위공채 성적예측 [2] 모집단위"
        db_table = 'a_predict_police_unit'


class PoliceDepartment(Department):
    # Override parent abstract model fields
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.police_exam_choices, default='경위', verbose_name='시험')
    unit = models.CharField(
        max_length=20, choices=ChoiceMethod.police_unit_choices,
        default='경위', verbose_name='모집단위')
    name = models.CharField(
        max_length=40, choices=ChoiceMethod.police_department_choices,
        default='일반', verbose_name='직렬')

    class Meta:
        verbose_name = verbose_name_plural = "경위공채 성적예측 [3] 직렬"
        db_table = 'a_predict_police_department'


class PoliceStudent(Student):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_next_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.police_exam_choices, default='경위', verbose_name='시험')
    unit = models.CharField(
        max_length=20, choices=ChoiceMethod.police_unit_choices,
        default='경위', verbose_name='모집단위')
    department = models.CharField(
        max_length=40, choices=ChoiceMethod.police_department_choices,
        default='일반', verbose_name='직렬')
    selection = models.CharField(
        max_length=20, choices=ChoiceMethod.police_subject_choices, default='minbeob', verbose_name='선택과목')

    class Meta:
        verbose_name = verbose_name_plural = "경위공채 성적예측 [4] 수험정보"
        db_table = 'a_predict_police_student'


class PoliceAnswerCount(AnswerCount):
    # Override parent abstract model fields
    year = models.IntegerField(
        choices=ChoiceMethod.year_choices, default=ChoiceMethod.get_next_year(), verbose_name='연도')
    exam = models.CharField(
        max_length=2, choices=ChoiceMethod.police_exam_choices, default='경위', verbose_name='시험')
    subject = models.CharField(
        max_length=20, choices=ChoiceMethod.police_subject_choices, default='hyeongsa', verbose_name='과목')
    count_5 = None

    class Meta:
        verbose_name = verbose_name_plural = "경위공채 성적예측 [5] 답안개수"
        db_table = 'a_predict_police_answer_count'
