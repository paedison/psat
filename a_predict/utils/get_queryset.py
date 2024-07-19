from django.db.models import F


def get_student(request, exam_vars):
    if request.user.is_authenticated:
        return exam_vars.student_model.objects.filter(
            **exam_vars.exam_info, user=request.user).first()


def get_exam(exam_vars):
    return exam_vars.exam_model.objects.filter(**exam_vars.exam_info).first()


def get_units(exam_vars):
    return exam_vars.unit_model.objects.filter(exam=exam_vars.exam_exam).values_list('name', flat=True)


def get_location(exam_vars):
    serial = int(exam_vars.student.serial)
    if exam_vars.location_model:
        return exam_vars.location_model.objects.filter(
            **exam_vars.exam_info, serial_start__lte=serial, serial_end__gte=serial).first()


def get_qs_department(exam_vars, unit=None):
    if unit:
        return exam_vars.department_model.objects.filter(
            exam=exam_vars.exam_exam, unit=unit).order_by('id')
    return exam_vars.department_model.objects.filter(exam=exam_vars.exam_exam).order_by('order')


def get_qs_student(exam_vars):
    return exam_vars.student_model.objects.filter(**exam_vars.exam_info)


def get_qs_answer_count(exam_vars):
    return exam_vars.answer_count_model.objects.filter(**exam_vars.exam_info).annotate(
        no=F('number')).order_by('subject', 'number')
