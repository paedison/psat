import vanilla

from .viewmixins import lecture_view_mixins


class ListView(
    lecture_view_mixins.ListViewMixin,
    vanilla.TemplateView,
):
    template_name = 'lecture/v1/lecture_list.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#list_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        lecture_list = self.get_lecture_list()
        return super().get_context_data(
            info=self.info,
            icon_menu=self.ICON_MENU['lecture'],
            title='강의 목록',
            lecture_list=lecture_list,
            **kwargs,
        )


class DetailView(
    lecture_view_mixins.DetailViewMixin,
    vanilla.TemplateView,
):
    template_name = 'lecture/v1/lecture_detail.html'

    def get_template_names(self):
        htmx_template = {
            'False': self.template_name,
            'True': f'{self.template_name}#detail_main',
        }
        return htmx_template[f'{bool(self.request.htmx)}']

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk')
        lecture = self.get_lecture(pk)
        prev_lec, next_lec = self.get_prev_next_lecture(lecture)
        lec_images = self.get_lecture_images(lecture)
        lecture_list = self.get_lecture_list()
        return super().get_context_data(
            info=self.info,
            icon_menu=self.ICON_MENU['lecture'],
            icon_nav=self.ICON_NAV,
            title='강의 목록',
            lecture=lecture,
            prev_lec=prev_lec,
            next_lec=next_lec,
            lec_images=lec_images,
            lecture_list=lecture_list,
            **kwargs,
        )
