from django.core.management.base import BaseCommand
from django.db.models import F

from a_predict import models, utils
from predict import models as old_predict_models

PSAT_VARS = {
    'sub_list': ['헌법', '언어', '자료', '상황'],
    'subject_list': ['헌법', '언어논리', '자료해석', '상황판단'],
    'subject_fields': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang'],
    'score_fields': ['heonbeob', 'eoneo', 'jaryo', 'sanghwang', 'psat_avg'],
    'psat_fields': ['eoneo', 'jaryo', 'sanghwang'],
    'subject_vars': {
        '헌법': ('헌법', 'heonbeob'),
        '언어': ('언어논리', 'eoneo'),
        '자료': ('자료해석', 'jaryo'),
        '상황': ('상황판단', 'sanghwang'),
        '평균': ('PSAT 평균', 'psat_avg'),
    },
    'field_vars': {
        'heonbeob': ('헌법', '헌법'),
        'eoneo': ('언어', '언어논리'),
        'jaryo': ('자료', '자료해석'),
        'sanghwang': ('상황', '상황판단'),
        'psat_avg': ('평균', 'PSAT 평균'),
    },
    'problem_count': {'heonbeob': 25, 'eoneo': 40, 'jaryo': 40, 'sanghwang': 40},
    'rank_list': ['all_rank', 'low_rank', 'mid_rank', 'top_rank'],
    'old_answer_model': old_predict_models.Answer
}


def get_exam_vars(exam_info: dict):
    exam_vars = {
        'year': exam_info['year'],
        'exam': exam_info['exam'],
        'round': exam_info['round'],
        'info': exam_info,
    }
    if exam_info['exam'] == '행시':
        exam_vars.update(PSAT_VARS)
        exam_vars.update({
            'exam_model': models.PsatExam,
            'student_model': models.PsatStudent,
            'answer_count_model': models.PsatAnswerCount,
            'department_model': models.PsatDepartment,
        })
    return exam_vars


class Command(BaseCommand):
    help = 'Calculate Scores'

    def add_arguments(self, parser):
        parser.add_argument('exam_year', type=str, help='Year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam type')  # 행시
        parser.add_argument('exam_round', type=str, help='Round')  # 0

    def handle(self, *args, **kwargs):
        exam_year = kwargs['exam_year']
        exam_exam = kwargs['exam_exam']
        exam_round = kwargs['exam_round']
        exam_info = {'year': exam_year, 'exam': exam_exam, 'round': exam_round}

        # Set up exam_vars
        exam_vars = get_exam_vars(exam_info=exam_info)
        exam_model = exam_vars['exam_model']
        department_model = exam_vars['department_model']
        student_model = exam_vars['student_model']
        answer_count_model = exam_vars['answer_count_model']

        answer_official = exam_model.objects.get(**exam_info).answer_official

        # Create or update student_model instances
        old_students = old_predict_models.Student.objects.filter(
            exam__ex=exam_exam, exam__round=exam_round).annotate(created_at=F('timestamp'))
        student_data = utils.get_student_model_data(
            exam_vars=exam_vars, old_students=old_students)
        student_update_fields = ['answer', 'answer_count', 'answer_confirmed', 'answer_all_confirmed_at']
        utils.create_or_update_model(
            model=student_model, update_fields=student_update_fields, model_data=student_data)

        # Update exam_model for participants
        qs_student = student_model.objects.filter(**exam_info)
        exam = exam_model.objects.filter(**exam_info).first()
        participants = utils.get_participants(
            exam_vars=exam_vars, exam=exam, qs_student=qs_student)
        exam_model_data = utils.get_exam_model_data(exam=exam, participants=participants)
        utils.create_or_update_model(
            model=exam_model, update_fields=['participants'], model_data=exam_model_data)

        # Update student_model for score
        total_answer_lists, score_data = utils.get_total_answer_lists_and_score_data(
            exam_vars=exam_vars,
            qs_student=qs_student,
            answer_official=answer_official,
        )
        utils.create_or_update_model(
            model=student_model, update_fields=['score'], model_data=score_data)

        # Update student_model for rank
        rank_data = utils.get_rank_data(exam_vars=exam_vars, exam=exam, qs_student=qs_student)
        utils.create_or_update_model(
            model=student_model,
            update_fields=['rank'],
            model_data=rank_data,
        )

        # Create or update student_model for answer count
        all_count_dict = utils.get_all_count_dict(
            exam_vars=exam_vars, total_answer_lists=total_answer_lists)
        answer_count_matching_fields = [
            'count_1', 'count_2', 'count_3', 'count_4', 'count_5',
            'count_0', 'count_multiple', 'count_total',
        ]
        answer_count_data = utils.get_answer_count_model_data(
            exam_vars=exam_vars,
            matching_fields=answer_count_matching_fields,
            all_count_dict=all_count_dict,
        )
        utils.create_or_update_model(
            model=answer_count_model,
            update_fields=answer_count_matching_fields,
            model_data=answer_count_data,
        )

        # Update exam_model for statistics
        qs_department = department_model.objects.filter(exam=exam_vars['exam']).order_by('id')
        statistics = utils.get_statistics(
            exam_vars=exam_vars, exam=exam, qs_department=qs_department, qs_student=qs_student)
        statistics_data = utils.get_statistics_data(exam=exam, statistics=statistics)
        utils.create_or_update_model(
            model=exam_model, update_fields=['statistics'], model_data=statistics_data)

        # Update answer_count_model by rank
        total_answer_lists = utils.get_total_answer_lists_by_category(
            exam_vars=exam_vars, exam=exam, qs_student=qs_student)
        total_count_dict = utils.get_total_count_dict_by_category(
            exam_vars=exam_vars, total_answer_lists=total_answer_lists)
        total_answer_count_data = utils.get_total_answer_count_model_data(
            exam_vars=exam_vars,
            matching_fields=['all', 'filtered'],
            all_count_dict=total_count_dict,
        )
        utils.create_or_update_model(
            model=answer_count_model,
            update_fields=['all', 'filtered'],
            model_data=total_answer_count_data,
        )
