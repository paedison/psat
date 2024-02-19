from django.core.management.base import BaseCommand
from django.db import transaction

from score.models import predict_score_models as old_models
from predict.models import predict_models as new_models


class Command(BaseCommand):
    # def add_arguments(self, parser):
    #     parser.add_argument()

    def handle(self, *args, **options):
        old_students = old_models.PredictStudent.objects.all()
        old_answers = old_models.PredictAnswer.objects.select_related('student').all()
        old_answer_counts = old_models.PredictAnswerCount.objects.all()
        old_statistics = old_models.PredictStatistics.objects.select_related('student').all()
        old_statistics_virtual = old_models.PredictStatisticsVirtual.objects.select_related('student').all()

        with transaction.atomic():
            for old_student in old_students:
                new_exam = new_models.Exam.objects.get(
                    category='Prime',
                    year=old_student.year,
                    ex=old_student.ex,
                    round=old_student.round,
                )
                new_models.Student.objects.get_or_create(
                    exam=new_exam,
                    user_id=old_student.user_id,
                    name=old_student.name,
                    serial=old_student.serial,
                    password=old_student.password,
                    department_id=old_student.department_id,
                )

        with transaction.atomic():
            for old_answer in old_answers:
                new_student = new_models.Student.objects.get(
                    exam__category='Prime',
                    exam__year=old_answer.student.year,
                    exam__ex=old_answer.student.ex,
                    exam__round=old_answer.student.round,
                    user_id=old_answer.student.user_id,
                    name=old_answer.student.name,
                    serial=old_answer.student.serial,
                    password=old_answer.student.password,
                    department_id=old_answer.student.department_id,
                )
                new_answer, created = new_models.Answer.objects.get_or_create(
                    student=new_student,
                    sub=old_answer.sub,
                    is_confirmed=old_answer.is_confirmed,
                )
                if created:
                    for i in range(1, 41):
                        setattr(new_answer, f'prob{i}', getattr(old_answer, f'prob{i}'))
                    new_answer.save()

        with transaction.atomic():
            for old_answer_count in old_answer_counts:
                new_exam = new_models.Exam.objects.get(
                    category='Prime',
                    year=old_answer_count.year,
                    ex=old_answer_count.ex,
                    round=old_answer_count.round,
                )
                new_answer_count, created = new_models.AnswerCount.objects.get_or_create(
                    exam=new_exam,
                    sub=old_answer_count.sub,
                    number=old_answer_count.number,
                    answer=old_answer_count.answer,
                )
                if created:
                    new_answer_count.count_total = old_answer_count.count_total
                    for i in range(6):
                        setattr(new_answer_count, f'count_{i}', getattr(old_answer_count, f'count_{i}'))
                    new_answer_count.save()

        with transaction.atomic():
            for old_statistic in old_statistics:
                new_student = new_models.Student.objects.get(
                    exam__category='Prime',
                    exam__year=old_statistic.student.year,
                    exam__ex=old_statistic.student.ex,
                    exam__round=old_statistic.student.round,
                    user_id=old_statistic.student.user_id,
                    name=old_statistic.student.name,
                    serial=old_statistic.student.serial,
                    password=old_statistic.student.password,
                    department_id=old_statistic.student.department_id,
                )
                new_statistic, created = new_models.Statistics.objects.get_or_create(student=new_student)
                if created:
                    new_statistic.score_heonbeob = old_statistic.score_heonbeob
                    new_statistic.score_eoneo = old_statistic.score_eoneo
                    new_statistic.score_jaryo = old_statistic.score_jaryo
                    new_statistic.score_sanghwang = old_statistic.score_sanghwang
                    new_statistic.score_psat = old_statistic.score_psat
                    new_statistic.score_psat_avg = old_statistic.score_psat_avg

                    new_statistic.rank_total_heonbeob = old_statistic.rank_total_heonbeob
                    new_statistic.rank_total_eoneo = old_statistic.rank_total_eoneo
                    new_statistic.rank_total_jaryo = old_statistic.rank_total_jaryo
                    new_statistic.rank_total_sanghwang = old_statistic.rank_total_sanghwang
                    new_statistic.rank_total_psat = old_statistic.rank_total_psat

                    new_statistic.rank_department_heonbeob = old_statistic.rank_department_heonbeob
                    new_statistic.rank_department_eoneo = old_statistic.rank_department_eoneo
                    new_statistic.rank_department_jaryo = old_statistic.rank_department_jaryo
                    new_statistic.rank_department_sanghwang = old_statistic.rank_department_sanghwang
                    new_statistic.rank_department_psat = old_statistic.rank_department_psat

                    new_statistic.rank_ratio_total_heonbeob = old_statistic.rank_ratio_total_heonbeob
                    new_statistic.rank_ratio_total_eoneo = old_statistic.rank_ratio_total_eoneo
                    new_statistic.rank_ratio_total_jaryo = old_statistic.rank_ratio_total_jaryo
                    new_statistic.rank_ratio_total_sanghwang = old_statistic.rank_ratio_total_sanghwang
                    new_statistic.rank_ratio_total_psat = old_statistic.rank_ratio_total_psat

                    new_statistic.rank_ratio_department_heonbeob = old_statistic.rank_ratio_department_heonbeob
                    new_statistic.rank_ratio_department_eoneo = old_statistic.rank_ratio_department_eoneo
                    new_statistic.rank_ratio_department_jaryo = old_statistic.rank_ratio_department_jaryo
                    new_statistic.rank_ratio_department_sanghwang = old_statistic.rank_ratio_department_sanghwang
                    new_statistic.rank_ratio_department_psat = old_statistic.rank_ratio_department_psat

                    new_statistic.save()

        with transaction.atomic():
            for old_statistic_virtual in old_statistics_virtual:
                new_student = new_models.Student.objects.get(
                    exam__category='Prime',
                    exam__year=old_statistic_virtual.student.year,
                    exam__ex=old_statistic_virtual.student.ex,
                    exam__round=old_statistic_virtual.student.round,
                    user_id=old_statistic_virtual.student.user_id,
                    name=old_statistic_virtual.student.name,
                    serial=old_statistic_virtual.student.serial,
                    password=old_statistic_virtual.student.password,
                    department_id=old_statistic_virtual.student.department_id,
                )
                new_statistic_virtual, created = new_models.StatisticsVirtual.objects.get_or_create(student=new_student)
                if created:
                    new_statistic_virtual.score_heonbeob = old_statistic_virtual.score_heonbeob
                    new_statistic_virtual.score_eoneo = old_statistic_virtual.score_eoneo
                    new_statistic_virtual.score_jaryo = old_statistic_virtual.score_jaryo
                    new_statistic_virtual.score_sanghwang = old_statistic_virtual.score_sanghwang
                    new_statistic_virtual.score_psat = old_statistic_virtual.score_psat
                    new_statistic_virtual.score_psat_avg = old_statistic_virtual.score_psat_avg

                    new_statistic_virtual.save()
