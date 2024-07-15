from django.db.models import F


def get_student(request, exam_vars: dict):
    if request.user.is_authenticated:
        return exam_vars['student_model'].objects.filter(
            **exam_vars['exam_info'], user=request.user).first()


def get_exam(exam_vars: dict):
    return exam_vars['exam_model'].objects.filter(**exam_vars['exam_info']).first()


def get_location(exam_vars: dict, student):
    serial = int(student.serial)
    return exam_vars['location_model'].objects.filter(
        **exam_vars['exam_info'], serial_start__lte=serial, serial_end__gte=serial).first()


def get_qs_department(exam_vars: dict):
    return exam_vars['department_model'].objects.filter(exam=exam_vars['exam']).order_by('id')


def get_qs_student(exam_vars: dict):
    return exam_vars['student_model'].objects.filter(**exam_vars['exam_info'])


def get_qs_answer_count(exam_vars: dict):
    return exam_vars['answer_count_model'].objects.filter(**exam_vars['exam_info']).annotate(
        no=F('number')).order_by('subject', 'number')
