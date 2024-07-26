from django.core.management.base import BaseCommand

from .. import command_utils


class Command(BaseCommand):
    help = 'Setup predict data from old data'

    def add_arguments(self, parser):
        parser.add_argument('exam_type', type=str, help='Exam type')  # psat
        parser.add_argument('exam_year', type=str, help='Exam year')  # 2024
        parser.add_argument('exam_exam', type=str, help='Exam exam')  # 행시
        parser.add_argument('exam_round', type=str, help='Exam Round')  # 0

    def handle(self, *args, **kwargs):
        exam_type = kwargs['exam_type']
        exam_year = kwargs['exam_year']
        exam_exam = kwargs['exam_exam']
        exam_round = kwargs['exam_round']

        # Set up exam_vars
        exam_vars = command_utils.CommandPredictExamVars(None, exam_type, exam_year, exam_exam, exam_round)
        exam = exam_vars.exam_model.objects.get(**exam_vars.exam_info)

        self.stdout.write('================')
        self.stdout.write('Create or update student_model from old data')
        student_data, answer_lists = command_utils.get_student_data_answer_lists(exam_vars)
        command_utils.create_or_update_model(exam_vars.student_model, ['data'], student_data)

        self.stdout.write('================')
        self.stdout.write('Update student_model for data(score)')
        qs_student = exam_vars.student_model.objects.filter(**exam_vars.exam_info)
        score_data, score_lists = command_utils.get_score_data_score_lists(exam_vars, exam, qs_student, ['data'])
        command_utils.create_or_update_model(exam_vars.student_model, ['data'], score_data)

        self.stdout.write('================')
        self.stdout.write('Update student_model for rank')
        rank_data = command_utils.get_rank_data(exam_vars, exam, qs_student, score_lists)
        command_utils.create_or_update_model(exam_vars.student_model, ['rank'], rank_data)

        self.stdout.write('================')
        self.stdout.write('Update exam_model for participants')
        participants = command_utils.get_participants(exam_vars, exam, qs_student)
        exam_model_data = command_utils.get_exam_model_data(exam, participants)
        command_utils.create_or_update_model(exam_vars.exam_model, ['participants'], exam_model_data)

        self.stdout.write('================')
        self.stdout.write('Update exam_model for statistics')
        qs_department = command_utils.get_qs_department(exam_vars)
        statistics = command_utils.get_statistics(exam_vars, exam, qs_department, qs_student)
        statistics_data = command_utils.get_statistics_data(exam, statistics)
        command_utils.create_or_update_model(exam_vars.exam_model, ['statistics'], statistics_data)

        self.stdout.write('================')
        self.stdout.write('Update answer_count_model')
        count_lists = command_utils.get_count_lists(exam_vars, exam, answer_lists)
        answer_fields = exam_vars.count_fields + ['count_multiple', 'count_total', 'answer']
        answer_count_data = command_utils.get_answer_count_model_data(exam_vars, answer_fields, count_lists)
        command_utils.create_or_update_model(exam_vars.answer_count_model, answer_fields, answer_count_data)

        self.stdout.write('================')
        self.stdout.write('Update answer_count_model by rank')
        answer_lists_by_category = command_utils.get_total_answer_lists_by_category(exam_vars, exam, qs_student)
        total_count_dict = command_utils.get_total_count_dict_by_category(exam_vars, answer_lists_by_category)
        total_answer_count_data = command_utils.get_total_answer_count_model_data(
            exam_vars, ['all', 'filtered'], total_count_dict)
        command_utils.create_or_update_model(
            exam_vars.answer_count_model, ['all', 'filtered'], total_answer_count_data)
