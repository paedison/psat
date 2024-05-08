import vanilla

from common.constants import icon_set
from common.views.base_views import HtmxHttpRequest

lectures = [
    {
        'id': 1,
        'title': '독해력 끌어올리기',
        'sub_title': '기초부터 시작하는 제대로 된 글읽기 훈련',
        'youtube_id': 'dPBQf5upilw',
        'subject': '언어논리',
    },
    {
        'id': 2,
        'title': '사칙연산 정복하기',
        'sub_title': '유효숫자, 보수, 덧셈, 뺄셈, 곱셈, 나눗셈',
        'youtube_id': 'hqEu18Y8qCk',
        'subject': '자료해석',
    },
    {
        'id': 3,
        'title': '법조문과 친해지기',
        'sub_title': '법조문의 체계, 형식, 내용',
        'youtube_id': 'jmA_KHFKGvo',
        'subject': '상황판단',
    },
    {
        'id': 4,
        'title': '핵심논지 파악하기',
        'sub_title': '논지 파악하기, 주장 비교하기, 빈칸 채우기',
        'youtube_id': '7g2i0xDFt9g',
        'subject': '언어논리',
    },
    {
        'id': 5,
        'title': '곱셈·분수 비교하기',
        'sub_title': '분수, 비율과 증가율, 곱셈·분수 비교하기',
        'youtube_id': 'kheVM68VzqQ',
        'subject': '자료해석',
    },
    {
        'id': 6,
        'title': '논리와 명제',
        'sub_title': '명제의 개념, 논리 연산자, 논리 법칙 및 공식',
        'youtube_id': 'RB5ifzRYFQ0',
        'subject': '언어논리',
    },
    {
        'id': 7,
        'title': '비율 심화개념',
        'sub_title': '변화율, 배율, 지수, 전체값, 여사건, 전체비',
        'youtube_id': 'AH7PZ-hZ4dE',
        'subject': '자료해석',
    },
]


class ListView(
    icon_set.ConstantIconSet,
    vanilla.TemplateView,
):
    request: HtmxHttpRequest
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
        info = {
            'menu': 'score',
        }
        icon_menu = self.ICON_MENU['lecture']
        for lecture in lectures:
            youtube_id = lecture['youtube_id']
            lecture['youtube_url'] = f'https://youtu.be/{youtube_id}/'
            lecture['thumbnail_url'] = f'https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg'
        return super().get_context_data(
            info=info,
            icon_menu=icon_menu,
            title='강의 목록',
            lectures=lectures,
            **kwargs,
        )


class DetailView(
    icon_set.ConstantIconSet,
    vanilla.TemplateView,
):
    request: HtmxHttpRequest
    kwargs: dict

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
        pk = self.kwargs.get('pk') - 1
        info = {
            'menu': 'score',
        }
        lecture = lectures[pk]
        icon_menu = self.ICON_MENU['lecture']
        youtube_id = lecture['youtube_id']
        lecture['youtube_url'] = f'https://youtu.be/{youtube_id}/'
        lecture['src'] = f'https://www.youtube.com/embed/{youtube_id}'
        return super().get_context_data(
            info=info,
            icon_menu=icon_menu,
            title='강의 목록',
            lecture=lecture,
            **kwargs,
        )
