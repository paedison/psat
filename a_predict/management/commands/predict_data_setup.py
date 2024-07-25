from django.core.management.base import BaseCommand
from django.db.models import F

from a_predict import utils
from a_predict.views.old_base_info import PsatExamVars
from predict import models as old_predict_models


class CommandPsatExamVars(PsatExamVars):
    old_answer_model = old_predict_models.Answer


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

        # Set up exam_vars
        exam_vars = CommandPsatExamVars(exam_year, exam_exam, exam_round)
        exam_model = exam_vars.exam_model
        student_model = exam_vars.student_model
        answer_count_model = exam_vars.answer_count_model
        exam_vars.exam = exam_model.objects.get(**exam_vars.exam_info)

        self.stdout.write('================')
        self.stdout.write('Create or update student_model from old data')
        old_students = old_predict_models.Student.objects.filter(
            exam__ex=exam_exam, exam__round=exam_round).annotate(created_at=F('timestamp'))
        student_data = utils.get_student_model_data(exam_vars, old_students)
        student_update_fields = ['answer', 'answer_count', 'answer_confirmed', 'answer_all_confirmed_at']
        utils.create_or_update_model(student_model, student_update_fields, student_data)

        self.stdout.write('================')
        self.stdout.write('Update student_model for score')
        qs_student = student_model.objects.filter(**exam_vars.exam_info)
        total_answer_lists, score_data = utils.get_total_answer_lists_and_score_data(exam_vars, qs_student)
        utils.create_or_update_model(student_model, ['score'], score_data)

        self.stdout.write('================')
        self.stdout.write('Update student_model for rank')
        rank_data = utils.get_rank_data(exam_vars, qs_student)
        utils.create_or_update_model(student_model, ['rank'], rank_data)

        self.stdout.write('================')
        self.stdout.write('Update exam_model for participants')
        participants = utils.get_participants(exam_vars, qs_student)
        exam_model_data = utils.get_exam_model_data(exam_vars, participants)
        utils.create_or_update_model(exam_model, ['participants'], exam_model_data)

        self.stdout.write('================')
        self.stdout.write('Update exam_model for statistics')
        qs_department = utils.get_qs_department(exam_vars)
        statistics = utils.get_statistics(exam_vars, qs_department, qs_student)
        statistics_data = utils.get_statistics_data(exam_vars, statistics)
        utils.create_or_update_model(exam_model, ['statistics'], statistics_data)

        self.stdout.write('================')
        self.stdout.write('Update answer_count_model')
        all_count_dict = utils.get_all_count_dict(exam_vars, total_answer_lists)
        answer_fields = exam_vars.count_fields + ['count_multiple', 'count_total']
        answer_count_data = utils.get_answer_count_model_data(exam_vars, answer_fields, all_count_dict)
        utils.create_or_update_model(answer_count_model, answer_fields, answer_count_data)

        self.stdout.write('================')
        self.stdout.write('Update answer_count_model by rank')
        total_answer_lists = utils.get_total_answer_lists_by_category(exam_vars, qs_student)
        total_count_dict = utils.get_total_count_dict_by_category(exam_vars, total_answer_lists)
        total_answer_count_data = utils.get_total_answer_count_model_data(
            exam_vars, ['all', 'filtered'], total_count_dict)
        utils.create_or_update_model(
            answer_count_model, ['all', 'filtered'], total_answer_count_data)
