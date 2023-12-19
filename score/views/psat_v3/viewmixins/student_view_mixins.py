from django.db.models import F

from . import base_mixins


class StudentCreateModalViewMixin(base_mixins.BaseMixin):
    units: any
    header: str

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'header': self.header,
            'year': self.year,
            'ex': self.ex,
            'units': self.units,
        }

    def get_properties(self):
        super().get_properties()

        self.units = self.unit_model.objects.filter(exam=self.exam)
        self.header = f'{self.year}년 {self.exam.name} 수험 정보 입력'


class CreateDepartmentMixin(base_mixins.BaseMixin):
    unit_id: str
    departments: any

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {'departments': self.departments}

    def get_properties(self):
        super().get_properties()

        self.unit_id = self.request.POST.get('unit_id')
        self.departments = self.department_model.objects.filter(unit_id=self.unit_id)


class StudentUpdateModalViewMixin(base_mixins.BaseMixin):
    student_id: str
    student: any
    units: any
    header: str
    departments: any

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'header': self.header,
            'student': self.student,
            'units': self.units,
            'departments': self.departments,
        }

    def get_properties(self):
        super().get_properties()

        self.student_id = self.kwargs['student_id']
        self.student = self.get_student()
        self.units = self.unit_model.objects.filter(exam=self.student.department.unit.exam)
        self.header = f'{self.student.year}년 {self.student.exam} 수험 정보 수정'
        self.departments = (
            self.department_model.objects.filter(unit=self.student.department.unit)
            .select_related('unit')
        )

    def get_student(self):
        """ Return student instance for requested student ID. """

        return (
            self.student_model.objects
            .annotate(ex=F('department__unit__exam__abbr'), exam=F('department__unit__exam__name'))
            .select_related('department__unit', 'department__unit__exam')
            .get(id=self.student_id)
        )


class UpdateDepartmentMixin(base_mixins.BaseMixin):
    unit_id: str
    student_id: str
    departments: any
    student: any

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            'departments': self.departments,
            'student': self.student,
        }

    def get_properties(self):
        super().get_properties()

        self.unit_id = self.request.POST.get('unit_id')
        self.student_id = self.kwargs.get('student_id')
        self.departments = self.department_model.objects.filter(unit_id=self.unit_id)
        self.student = self.student_model.objects.get(id=self.student_id)
