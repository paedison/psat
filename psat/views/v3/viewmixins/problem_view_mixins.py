from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q, Value, CharField
from django.db.models.functions import Concat, Cast
from django.urls import reverse_lazy

from common.constants.icon_set import ConstantIconSet
from dashboard.models import psat_data_models
from psat import models as custom_models
from reference.models import psat_models as reference_models


class BaseMixin(ConstantIconSet):
    menu = 'psat'

    request: any
    kwargs: dict

    user_id: int | None
    view_type: str
    info: dict

    year: str
    ex: str
    sub: str
    page_number: str
    psat: reference_models.Psat.objects

    sub_title_dict: dict[str, dict[str, str]]
    sub_title: str

    is_liked: str
    rating: str
    is_correct: str
    has_memo: str
    has_tag: str
    search_data: str

    ip_address: str

    url_options: str
    base_url: str
    pagination_url: str

    custom_data: dict[str, reference_models.PsatProblem.objects]
    like_data: reference_models.PsatProblem.objects
    rate_data: reference_models.PsatProblem.objects
    solve_data: reference_models.PsatProblem.objects
    memo_data: reference_models.PsatProblem.objects
    tag_data: reference_models.PsatProblem.objects

    def get_properties(self):
        self.user_id = self.request.user.id if self.request.user.is_authenticated else None
        self.view_type = self.kwargs.get('view_type', 'problem')
        self.info = self.get_info()

        self.year = self.request.GET.get('year', '')
        self.ex = self.request.GET.get('ex', '')
        self.sub = self.request.GET.get('sub', '')
        self.psat = self.get_psat()
        self.page_number = self.request.GET.get('page', '1')

        self.is_liked = self.rating = self.is_correct = 'pass'
        self.has_memo = self.has_tag = self.search_data = 'pass'

        if self.view_type == 'like':
            self.is_liked = self.request.GET.get('is_liked', '')
        if self.view_type == 'rate':
            self.rating = self.request.GET.get('rating', '')
        if self.view_type == 'solve':
            self.is_correct = self.request.GET.get('is_correct', '')
        if self.view_type == 'memo':
            self.has_memo = self.request.GET.get('has_memo', '')
        if self.view_type == 'tag':
            self.has_tag = self.request.GET.get('has_tag', '')
        if self.view_type == 'search':
            self.search_data = self.request.GET.get('data', '') or self.request.POST.get('data', '')

        self.sub_title_dict = self.get_sub_title_dict()
        self.sub_title = self.get_sub_title()

        self.ip_address = self.request.META.get('REMOTE_ADDR')
        self.url_options, self.base_url, self.pagination_url = self.get_urls()

        self.custom_data = self.get_custom_data()
        self.like_data = self.custom_data['like']
        self.rate_data = self.custom_data['rate']
        self.solve_data = self.custom_data['solve']
        self.memo_data = self.custom_data['memo']
        self.tag_data = self.custom_data['tag']

    def get_urls(self) -> tuple[str, str, str]:
        url_options = (
            f'?year={self.year}&ex={self.ex}&sub={self.sub}&page={self.page_number}'
            f'&is_liked={self.is_liked}&rating={self.rating}&is_correct={self.is_correct}'
            f'&has_memo={self.has_memo}&has_tag={self.has_tag}&data={self.search_data}'
        )
        base_url = reverse_lazy('psat:list', args=[self.view_type])
        pagination_url = f'{base_url}{url_options}'
        return url_options, base_url, pagination_url

    def get_psat(self) -> reference_models.Psat.objects:
        psat_filter = Q()
        if self.year:
            psat_filter &= Q(year=self.year)
        if self.ex:
            psat_filter &= Q(exam__abbr=self.ex)
        if self.sub:
            psat_filter &= Q(subject__abbr=self.sub)
        return reference_models.Psat.objects.filter(psat_filter).select_related('exam', 'subject').first()

    def get_sub_title_dict(self) -> dict[str, dict[str, str]]:
        return {
            'like': {
                '': '즐겨찾기 지정',
                'True': self.ICON_LIKE['true'] + '즐겨찾기 추가',
                'False': self.ICON_LIKE['false'] + '즐겨찾기 제외',
                'None': '즐겨찾기 미지정',
            },
            'rate': {
                '': '난이도 지정',
                '5': self.ICON_RATE['star5'],
                '4': self.ICON_RATE['star4'],
                '3': self.ICON_RATE['star3'],
                '2': self.ICON_RATE['star2'],
                '1': self.ICON_RATE['star1'],
                'None': '난이도 미지정',
            },
            'solve': {
                '': '정답 확인',
                'True': self.ICON_SOLVE['true'] + '맞힌 문제',
                'False': self.ICON_SOLVE['false'] + '틀린 문제',
                'None': '정답 미확인',
            },
            'memo': {
                '': self.ICON_MEMO['true'] + '메모 남긴 문제',
                'True': self.ICON_MEMO['true'] + '메모 남긴 문제',
                'False': self.ICON_MEMO['false'] + '메모 없는 문제',
                'None': self.ICON_MEMO['false'] + '메모 없는 문제',
            },
            'tag': {
                '': self.ICON_TAG['true'] + '태그 남긴 문제',
                'True': self.ICON_TAG['true'] + '태그 남긴 문제',
                'False': self.ICON_TAG['false'] + '태그 없는 문제',
                'None': self.ICON_TAG['false'] + '태그 없는 문제',
            }
        }

    def get_sub_title(self) -> str:
        title_snippet = {
            'problem': '기출문제',
            'search': '검색 결과'
        }
        key_dict = {
            'like': self.is_liked,
            'rate': self.rating,
            'solve': self.is_correct,
            'memo': self.has_memo,
            'tag': self.has_tag,
        }

        sub_title = ''
        if self.view_type in ['problem', 'search']:
            title_parts = []
            if self.year and not self.ex and not self.sub:  # year
                title_parts.append(f'{self.psat.year}년 PSAT')
            elif not self.year and self.ex and not self.sub:  # ex
                title_parts.append(f'{self.psat.exam.name} PSAT')
            elif not self.year and not self.ex and self.sub:  # sub
                title_parts.append(f'{self.psat.subject.name} PSAT')
            elif self.year and self.ex and not self.sub:  # year, ex
                title_parts.append(f'{self.psat.year}년 {self.psat.exam.name}')
            elif self.year and not self.ex and self.sub:  # year, sub
                title_parts.append(f'{self.psat.year}년 {self.psat.subject.name}')
            elif not self.year and self.ex and self.sub:  # ex, sub
                title_parts.append(f'{self.psat.exam.name} {self.psat.subject.name}')
            elif self.year and self.ex and self.sub:  # year, ex, sub
                title_parts.append(f'{self.psat.year}년 {self.psat.exam.name} {self.psat.subject.name}')
            elif not self.year and not self.ex and not self.sub:  # all
                title_parts.append(f'전체 PSAT')
            sub_title = f'{" ".join(title_parts)} {title_snippet[self.view_type]}'
        else:
            for key, item in key_dict.items():
                if key == self.view_type:
                    sub_title = self.sub_title_dict[key][item]

        return sub_title

    def get_info(self) -> dict[str, str]:
        """ Get the meta-info for the current view. """
        color_dict = {
            'problem': 'primary',
            'like': 'danger',
            'rate': 'warning',
            'solve': 'success',
            'search': 'primary',
            'memo': 'warning',
            'tag': 'primary',
        }
        return {
            'menu': 'psat',
            'view_type': self.view_type,
            'color': color_dict[self.view_type],
        }

    def get_custom_data(self) -> dict[str, reference_models.PsatProblem.objects]:
        """ Get all kinds of custom data. """
        problem_id = self.kwargs.get('problem_id')

        values_list_keys = ['id', 'psat_id', 'year', 'exam', 'subject', 'number']
        custom_data = (
            reference_models.PsatProblem.objects
            .annotate(year=F('psat__year'), exam=F('psat__exam__name'), subject=F('psat__subject__name'))
            .order_by('-psat__year', 'id'))

        if problem_id:
            problem = reference_models.PsatProblem.objects.get(id=problem_id)
            problem_data = custom_data.filter(psat_id=problem.psat_id).values(*values_list_keys)
        else:
            problem_data = {}

        if self.user_id:
            like_data = (
                self.get_list_queryset('like').annotate(is_liked=F('likes__is_liked'))
                .values(*values_list_keys, 'is_liked'))
            rate_data = (
                self.get_list_queryset('rate').annotate(rating=F('rates__rating'))
                .values(*values_list_keys, 'rating'))
            solve_data = (
                self.get_list_queryset('solve')
                .annotate(user_answer=F('solves__answer'), is_correct=F('solves__is_correct'))
                .values(*values_list_keys, 'user_answer', 'is_correct'))
            if self.has_memo:
                memo_data = custom_data.filter(memos__isnull=False, memos__user_id=self.user_id).values(*values_list_keys)
            else:
                memo_data = custom_data.exclude(memos__isnull=False, memos__user_id=self.user_id).values(*values_list_keys)
            if self.has_tag:
                tag_data = custom_data.filter(tags__isnull=False, tags__user_id=self.user_id).values(*values_list_keys)
            else:
                tag_data = custom_data.exclude(tags__isnull=False, tags__user_id=self.user_id).values(*values_list_keys)
        else:
            like_data = rate_data = solve_data = memo_data = tag_data = None

        return {
            'problem': problem_data,
            'like': like_data,
            'rate': rate_data,
            'solve': solve_data,
            'memo': memo_data,
            'tag': tag_data,
            'search': problem_data,
        }

    def get_list_queryset(self, view_type) -> reference_models.PsatProblem.objects:
        """ Get list queryset for current view type. """
        problem_filter = Q()
        if self.year != '':
            problem_filter &= Q(psat__year=self.year)
        if self.ex != '':
            problem_filter &= Q(psat__exam__abbr=self.ex)
        if self.sub != '':
            problem_filter &= Q(psat__subject__abbr=self.sub)

        queryset = (
            reference_models.PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name')))

        memos_isnull = not self.has_memo if self.has_memo in ['True', 'False'] else 'None'
        tags_isnull = not self.has_tag if self.has_tag in ['True', 'False'] else 'None'
        custom_field = {
            'problem': (None, 'pass'),
            'like': ('likes__is_liked', self.is_liked),
            'rate': ('rates__rating', self.rating),
            'solve': ('solves__is_correct', self.is_correct),
            'memo': ('memos__isnull', memos_isnull),
            'tag': ('tags__isnull', tags_isnull),
            'search': ('data__contains', self.search_data),
        }
        field, value = custom_field[view_type]

        if value == 'pass':
            pass
        elif value == '':
            problem_filter &= Q(**{f'{view_type}s__isnull': False})
        else:
            if value == 'None':
                return queryset.exclude(**{f'{view_type}s__user_id': self.user_id})
            elif value != '':
                problem_filter &= Q(**{field: value})

        user_id_filter = {
            'problem': {},
            'like': {'likes__user_id': self.user_id},
            'rate': {'rates__user_id': self.user_id},
            'solve': {'solves__user_id': self.user_id},
            'memo': {'memos__user_id': self.user_id},
            'tag': {'tags__user_id': self.user_id},
            'search': {},
        }
        problem_filter &= Q(**user_id_filter[view_type])

        return queryset.filter(problem_filter)


class ListViewMixIn(BaseMixin):
    title: str

    year_option: dict
    ex_option: dict
    sub_option: dict
    like_option: dict
    rate_option: dict
    solve_option: dict
    memo_option: dict
    tag_option: dict

    page_obj: any
    page_range: any

    def get_properties(self):
        super().get_properties()

        self.title = self.get_title()

        select_options = self.get_select_options()
        self.year_option = select_options['year_option']
        self.ex_option = select_options['ex_option']
        self.sub_option = select_options['sub_option']
        self.like_option = select_options['like_option']
        self.rate_option = select_options['rate_option']
        self.solve_option = select_options['solve_option']
        self.memo_option = select_options['memo_option']
        self.tag_option = select_options['tag_option']

        self.page_obj, self.page_range = self.get_paginator_info()

    def get_title(self) -> str:
        title_dict = {
            'problem': '기출문제',
            'like': '즐겨찾기',
            'rate': '난이도',
            'solve': '정답확인',
            'memo': '메모',
            'tag': '태그',
            'search': '검색 결과',
        }
        return title_dict[self.view_type]

    def get_queryset(self) -> reference_models.PsatProblem.objects:
        return self.get_list_queryset(self.view_type)

    def get_select_options(self) -> dict[str, dict]:
        queryset = self.get_queryset()

        year_list = (
            queryset.annotate(
                year=F('psat__year'),
                year_suffix=Cast(Concat(F('psat__year'), Value('년')), CharField()))
            .distinct().values_list('year', 'year_suffix').order_by('-psat__year'))
        ex_list = (
            queryset.annotate(ex=F('psat__exam__abbr'), exam=F('psat__exam__label'))
            .distinct().values_list('ex', 'exam').order_by('psat__exam_id'))
        sub_list = (
            queryset.annotate(sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .distinct().values_list('sub', 'subject').order_by('psat__subject_id'))
        new_sub_list = [(s[0], f'{self.ICON_SUBJECT[s[0]]}{s[1]}') for s in sub_list]

        def get_options(target: list) -> list[tuple]:
            target_option = []
            for t in target:
                if t not in target_option:
                    target_option.append(t)
            return target_option

        year_option = {
            'var': 'year',
            'text': '연도',
            'total': '전체 연도',
            'current': self.year,
            'options': get_options(year_list),
        }
        ex_option = {
            'var': 'ex',
            'text': '시험',
            'total': '전체 시험',
            'current': self.ex,
            'options': get_options(ex_list),
        }
        sub_option = {
            'var': 'sub',
            'text': '과목',
            'total': '전체 과목',
            'current': self.sub,
            'options': get_options(new_sub_list),
        }

        def get_view_url(view_type: str) -> str:
            return reverse_lazy('psat:list', args=[view_type])

        url_like = get_view_url('like')
        url_rate = get_view_url('rate')
        url_solve = get_view_url('solve')
        url_memo = get_view_url('memo')
        url_tag = get_view_url('tag')

        like_option = {
            'var': 'like',
            'text': self.ICON_LIKE['filter'],
            'current': self.is_liked,
            'options': [
                ('', '즐겨찾기 지정', f'{url_like}'),
                ('True', self.ICON_LIKE['true'] + '즐겨찾기 추가', f'{url_like}?is_liked=True'),
                ('False', self.ICON_LIKE['false'] + '즐겨찾기 제외', f'{url_like}?is_liked=False'),
                ('None', '즐겨찾기 미지정', f'{url_like}?is_liked=None'),
            ],
        }
        rate_option = {
            'var': 'rate',
            'text': self.ICON_RATE['filter'],
            'current': self.rating,
            'options': [
                ('', '난이도 지정', f'{url_rate}'),
                ('5', self.ICON_RATE['star5'], f'{url_rate}?rating=5'),
                ('4', self.ICON_RATE['star4'], f'{url_rate}?rating=4'),
                ('3', self.ICON_RATE['star3'], f'{url_rate}?rating=3'),
                ('2', self.ICON_RATE['star2'], f'{url_rate}?rating=2'),
                ('1', self.ICON_RATE['star1'], f'{url_rate}?rating=1'),
                ('None', '난이도 미지정', f'{url_rate}?rating=None'),
            ]
        }
        solve_option = {
            'var': 'solve',
            'text': self.ICON_SOLVE['filter'],
            'current': self.is_correct,
            'options': [
                ('', '정답 확인', f'{url_solve}'),
                ('True', self.ICON_SOLVE['true'] + '맞힌 문제', f'{url_solve}?is_correct=True'),
                ('False', self.ICON_SOLVE['false'] + '틀린 문제', f'{url_solve}?is_correct=False'),
                ('None', '정답 미확인', f'{url_solve}?is_correct=None'),
            ]
        }
        memo_option = {
            'var': 'memo',
            'text': self.ICON_MEMO['filter'],
            'current': self.has_memo,
            'options': [
                ('True', self.ICON_MEMO['true'] + '메모 남긴 문제', f'{url_memo}?has_memo=True'),
                ('False', self.ICON_MEMO['false'] + '메모 없는 문제', f'{url_memo}?has_memo=None'),
            ]
        }
        tag_option = {
            'var': 'tag',
            'text': self.ICON_TAG['filter'],
            'current': self.has_tag,
            'options': [
                ('True', self.ICON_TAG['true'] + '태그 남긴 문제', f'{url_tag}?has_tag=True'),
                ('False', self.ICON_TAG['false'] + '태그 없는 문제', f'{url_tag}?has_tag=None'),
            ]
        }

        return {
            'year_option': year_option,
            'ex_option': ex_option,
            'sub_option': sub_option,
            'like_option': like_option,
            'rate_option': rate_option,
            'solve_option': solve_option,
            'memo_option': memo_option,
            'tag_option': tag_option,
        }

    def get_paginator_info(self) -> tuple[object, object]:
        """ Get paginator, elided page range, and collect the evaluation info. """
        queryset = self.get_queryset()

        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(self.page_number)
        page_range = paginator.get_elided_page_range(number=self.page_number, on_each_side=3, on_ends=1)
        return page_obj, page_range


class DetailViewMixIn(BaseMixin):
    problem_id: int
    problem: reference_models.PsatProblem.objects
    memo: custom_models.Memo | None
    my_tag: custom_models.Tag | None

    view_custom_data: reference_models.PsatProblem.objects
    prev_prob: reference_models.PsatProblem.objects
    next_prob: reference_models.PsatProblem.objects
    list_data: list

    def get_properties(self):
        super().get_properties()

        self.problem_id = int(self.kwargs.get('problem_id'))
        self.problem = self.get_problem()

        self.memo = self.my_tag = None
        if self.request.user.is_authenticated:
            self.memo = custom_models.Memo.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()
            self.my_tag = custom_models.Tag.objects.filter(user_id=self.user_id, problem_id=self.problem_id).first()

        self.view_custom_data = self.custom_data[self.view_type]
        self.prev_prob, self.next_prob = self.get_prev_next_prob(self.view_custom_data)
        self.list_data = self.get_list_data(self.view_custom_data)

    def get_problem(self) -> reference_models.PsatProblem.objects:
        return (
            reference_models.PsatProblem.objects.only('id', 'psat_id', 'number', 'answer', 'question')
            .select_related('psat', 'psat__exam', 'psat__subject')
            .prefetch_related('likes', 'rates', 'solves')
            .annotate(
                year=F('psat__year'), ex=F('psat__exam__abbr'), exam=F('psat__exam__name'),
                sub=F('psat__subject__abbr'), subject=F('psat__subject__name'))
            .get(id=self.problem_id)
        )

    def get_find_filter(self) -> dict:
        find_filter = {
            'problem_id': self.problem_id,
            'user_id': self.user_id,
        }
        if not self.user_id:
            find_filter['ip_address'] = self.ip_address
        return find_filter

    def get_open_instance(self):
        find_filter = self.get_find_filter()
        with transaction.atomic():
            instance, is_created = custom_models.Open.objects.get_or_create(**find_filter)
            recent_log = psat_data_models.PsatOpenLog.objects.filter(**find_filter).last()
            if recent_log:
                repetition = recent_log.repetition + 1
            else:
                repetition = 1
            create_filter = find_filter.copy()
            extra_filter = {
                'data_id': instance.id,
                'repetition': repetition,
            }
            create_filter.update(extra_filter)
            psat_data_models.PsatOpenLog.objects.create(**create_filter)

    def get_prev_next_prob(self, custom_data: reference_models.PsatProblem.objects) -> tuple:
        if self.request.method == 'GET':
            custom_list = list(custom_data.values_list('id', flat=True))
            prev_prob = next_prob = None
            last_id = len(custom_list) - 1
            try:
                q = custom_list.index(self.problem_id)
                if q != 0:
                    prev_prob = custom_data[q - 1]
                    prev_prob['icon'] = f'{self.ICON_NAV["prev_prob"]}'
                if q != last_id:
                    next_prob = custom_data[q + 1]
                    next_prob['icon'] = f'{self.ICON_NAV["next_prob"]}'
                return prev_prob, next_prob
            except ValueError:
                return None, None

    def get_list_data(self, custom_data) -> list:
        def get_view_list_data():
            organized_dict = {}
            organized_list = []
            for prob in custom_data:
                key = prob['psat_id']
                if key not in organized_dict:
                    organized_dict[key] = []
                year, exam, subject = prob['year'], prob['exam'], prob['subject']
                problem_url = reverse_lazy(
                    'psat:detail',
                    kwargs={'view_type': self.view_type, 'problem_id': prob['id']}
                )
                list_item = {
                    'exam_name': f"{year}년 {exam} {subject}",
                    'problem_number': prob['number'],
                    'problem_id': prob['id'],
                    'problem_url': problem_url
                }
                organized_dict[key].append(list_item)

            for key, items in organized_dict.items():
                num_empty_instances = 5 - (len(items) % 5)
                if num_empty_instances < 5:
                    items.extend([None] * num_empty_instances)
                for i in range(0, len(items), 5):
                    row = items[i:i+5]
                    organized_list.extend(row)
            return organized_list

        if self.view_type == 'problem':
            return get_view_list_data()
        elif self.view_type == 'like' and self.is_liked is not None:
            return get_view_list_data()
        elif self.view_type == 'rate' and self.rating is not None:
            return get_view_list_data()
        elif self.view_type == 'solve' and self.is_correct is not None:
            return get_view_list_data()
        elif self.view_type == 'memo' and self.has_memo:
            return get_view_list_data()
        elif self.view_type == 'tag' and self.has_tag:
            return get_view_list_data()
