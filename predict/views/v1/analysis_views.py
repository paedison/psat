import vanilla

from .viewmixins import analysis_view_mixins, base_mixins


class ListView(
    base_mixins.OnlyStaffAllowedMixin,
    analysis_view_mixins.ListViewMixin,
    vanilla.TemplateView
):
    template_name = 'predict/v1/analysis/predict_analysis_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            # 'info': self.info,
            'title': 'Score',

            # student_list
            'student_page_obj': self.student_page_obj,
            'student_page_range': self.student_page_range,
            'student_base_url': self.student_base_url,
            'student_pagination_url': self.student_pagination_url,
        }


class ListStudentView(
    base_mixins.OnlyStaffAllowedMixin,
    analysis_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'predict/v1/analysis/snippets/list_student_list.html'

    def post(self, request, *args, **kwargs):
        return self.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict:
        self.get_properties()

        return {
            # base info
            # 'info': self.info,
            'title': 'Score',

            # student_list
            'student_page_obj': self.student_page_obj,
            'student_page_range': self.student_page_range,
            'student_base_url': self.student_base_url,
            'student_pagination_url': self.student_pagination_url,
        }


list_view = ListView.as_view()
list_student_view = ListStudentView.as_view()
