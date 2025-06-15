__all__ = [
    'NormalListData', 'NormalDetailData',
    'NormalUpdateData', 'NormalAnnotateProblem',
    'AdminListData', 'AdminDetailData',
    'AdminCreateData', 'AdminUpdateData',
    'get_custom_data', 'get_custom_icons',
]

import base64
import itertools
import json
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static
from django.urls import reverse

from a_psat import models, filters, forms
from a_psat.utils.variables import RequestData, PsatData, get_prev_next_obj
from common.constants import icon_set_new
from common.models import User
from common.utils import get_paginator_context, HtmxHttpRequest
from common.utils.modify_models_methods import with_bulk_create_or_update, append_list_create


@dataclass(kw_only=True)
class ProblemData:
    request: HtmxHttpRequest
    problem: models.Problem

    def __post_init__(self):
        self._user = self.request.user if self.request.user.is_authenticated else None
        self.base_list_data = models.Problem.objects.base_list(self.problem)

    def get_problem_list_context(self):
        return {
            'list_title': '', 'color': 'primary',
            'list_data': self.get_list_data(self.base_list_data),
        }

    def get_like_list_context(self):
        like_list = models.Problem.objects.like_list(self.problem, self._user)
        return {
            'list_title': '즐겨찾기 추가 문제', 'color': 'danger',
            'list_data': self.get_list_data(like_list),
        }

    def get_rate_list_context(self):
        rate_list = models.Problem.objects.rate_list(self.problem, self._user)
        return {
            'list_title': '난이도 선택 문제', 'color': 'warning',
            'list_data': self.get_list_data(rate_list),
        }

    def get_solve_list_context(self):
        solve_list = models.Problem.objects.solve_list(self.problem, self._user)
        return {
            'list_title': '정답 확인 문제', 'color': 'success',
            'list_data': self.get_list_data(solve_list),
        }

    def get_memo_list_context(self):
        memo_list = models.Problem.objects.memo_list(self.problem, self._user)
        return {
            'list_title': '메모 작성 문제', 'color': 'warning',
            'list_data': self.get_list_data(memo_list),
        }

    def get_tag_list_context(self):
        tag_list = models.Problem.objects.tag_list(self.problem, self._user)
        return {
            'list_title': '태그 작성 문제', 'color': 'primary',
            'list_data': self.get_list_data(tag_list),
        }

    @staticmethod
    def get_list_data(custom_data) -> list:
        organized_dict = {}
        organized_list = []
        for prob in custom_data:
            year, exam, subject = prob.psat.year, prob.psat.exam, prob.subject
            key = f'{year}{exam[0]}{subject[0]}'
            if key not in organized_dict:
                organized_dict[key] = []
            problem_url = reverse('psat:problem-detail', args=[prob.id])
            list_item = {
                'exam_name': f"{year}년 {exam} {subject}",
                'problem_number': prob.number,
                'problem_id': prob.id,
                'problem_url': problem_url
            }
            organized_dict[key].append(list_item)

        for key, items in organized_dict.items():
            num_empty_instances = 5 - (len(items) % 5)
            if num_empty_instances < 5:
                items.extend([None] * num_empty_instances)
            for i in range(0, len(items), 5):
                row = items[i:i + 5]
                organized_list.extend(row)
        return organized_list

    def get_custom_data(self):
        custom_data = get_custom_data(self._user)
        get_custom_icons(self.problem, custom_data)
        return custom_data


@dataclass(kw_only=True)
class NormalListData:
    request: HtmxHttpRequest

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.keyword = request_data.keyword
        self.sub_title = request_data.get_sub_title()
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.filterset = request_data.get_filterset()

    def get_problem_context(self):
        custom_data = get_custom_data(self.request.user)
        problem_context = get_paginator_context(self.filterset.qs, self.page_number)
        if problem_context:
            for problem in problem_context['page_obj']:
                get_custom_icons(problem, custom_data)
            return problem_context

    def get_collections(self):
        if self.request.user.is_authenticated:
            return models.ProblemCollection.objects.user_collection(self.request.user)


@dataclass(kw_only=True)
class NormalDetailData:
    request: HtmxHttpRequest
    problem: models.Problem

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.process_image()
        self.problem_data = ProblemData(request=self.request, problem=self.problem)
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.filterset = request_data.get_filterset()
        self.prob_prev, self.prob_next = get_prev_next_obj(self.problem.pk, self.problem_data.base_list_data)
        self.custom_data = self.problem_data.get_custom_data()

    def process_image(self):
        img_normal = img_wide = {'alt': 'Preparing Image', 'src': static('image/preparing.png')}
        if self.problem.absolute_img_path.exists():
            img_normal = {'alt': 'Problem Image', 'src': self.problem.relative_img_path}
            img_wide = img_normal.copy()

            threshold_height = 2000
            img = Image.open(self.problem.absolute_img_path)
            width, height = img.size
            if height > threshold_height:
                temp_dir = settings.BASE_DIR / 'static/image/PSAT/temp_images'
                Path.mkdir(temp_dir, exist_ok=True)
                img_wide_filename = f'{self.problem.img_name}_wide.png'
                img_wide_path = temp_dir / img_wide_filename

                if not img_wide_path.exists():
                    create_img_wide(img, width, height, threshold_height, img_wide_path)
                img_wide['src'] = static(f'image/PSAT/temp_images/{img_wide_filename}')
        self.problem.img_normal = img_normal
        self.problem.img_wide = img_wide

    def get_prev_next_obj(self, custom_data) -> tuple:
        custom_list = list(custom_data.values_list('id', flat=True))
        prev_obj = next_obj = None
        last_id = len(custom_list) - 1
        try:
            q = custom_list.index(self.problem.pk)
            if q != 0:
                prev_obj = custom_data[q - 1]
            if q != last_id:
                next_obj = custom_data[q + 1]
            return prev_obj, next_obj
        except ValueError:
            return None, None

    def get_my_memo(self):
        for dt in self.custom_data['memo']:
            if dt.problem_id == self.problem.id:
                return models.ProblemMemo.objects.user_memo_for_problem(self.request.user, self.problem)

    def get_my_tags(self):
        for dt in self.custom_data['tag']:
            if dt.content_object_id == self.problem.id:
                return models.ProblemTag.objects.user_tags_for_problem(self.request.user, self.problem)
        return []


@dataclass(kw_only=True)
class NormalUpdateData:
    request: HtmxHttpRequest
    problem: models.Problem

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.view_type = request_data.view_type

    def get_like_problem_response(self):
        new_record = self.create_new_custom_record(models.ProblemLike)
        icon_like = icon_set_new.ICON_LIKE[f'{new_record.is_liked}']
        return HttpResponse(f'{icon_like}')

    def get_rate_problem_response(self, rating):
        _ = self.create_new_custom_record(models.ProblemRate, **{'rating': rating})
        icon_rate = icon_set_new.ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    def get_solve_problem_response_context(self, answer):
        is_correct = None
        if answer:
            answer = int(answer)
            is_correct = answer == self.problem.answer
            _ = self.create_new_custom_record(models.ProblemSolve, **{'answer': answer, 'is_correct': is_correct})
        return {
            'problem': self.problem, 'answer': answer, 'is_correct': is_correct,
            'icon_solve': icon_set_new.ICON_SOLVE[f'{is_correct}'],
        }

    def get_my_memo(self, content):
        return self.create_new_custom_record(models.ProblemMemo, **{'content': content})

    def create_new_custom_record(self, model, **kwargs):
        base_info = {'problem': self.problem, 'user': self.request.user, 'is_active': True}
        latest_record = model.objects.filter(**base_info).first()
        if latest_record:
            if isinstance(latest_record, models.ProblemLike):
                kwargs = {'is_liked': not latest_record.is_liked}
            with transaction.atomic():
                new_record = model.objects.create(**base_info, **kwargs)
                latest_record.is_active = False
                latest_record.save()
        else:
            new_record = model.objects.create(**base_info, **kwargs)
        return new_record


@dataclass(kw_only=True)
class NormalAnnotateProblem:
    request: HtmxHttpRequest
    pk: int

    def __post_init__(self):
        self.lookup_expr = {'problem_id': self.pk, 'user': self.request.user}
        self.problem: models.Problem = models.Problem.objects.filter(pk=self.pk).first()

    def process_post_request_to_save_annotation(self):
        try:
            data = json.loads(self.request.body)
            self.lookup_expr['annotate_type'] = data.get('annotateType')
            image_data = data.get('image')

            if not image_data.startswith('data:image/png;base64,'):
                return JsonResponse({'success': False, 'error': '이미지 형식이 잘못 설정되었습니다.'})

            self.lookup_expr['image'] = self.get_image_file(image_data)
            annotation = models.ProblemAnnotation.objects.create(**self.lookup_expr)
            return JsonResponse({'success': True, 'image_url': annotation.image.url})

        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': str(e)})

    def get_image_file(self, image_data):
        fmt, imgstr = image_data.split(';base64,')
        ext = fmt.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name=f'{self.problem.reference}_{uuid.uuid4()}.{ext}')

    def process_get_request_to_load_annotation(self):
        try:
            self.lookup_expr['annotate_type'] = self.request.GET.get('annotate_type')
            annotation = models.ProblemAnnotation.objects.filter(**self.lookup_expr).first()
            if annotation and annotation.image:
                return JsonResponse({'success': True, 'image_url': annotation.image.url})
            else:
                return JsonResponse({'success': False, 'error': 'No annotation found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@dataclass(kw_only=True)
class AdminListData:
    request: HtmxHttpRequest

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        self.sub_title = request_data.get_sub_title()
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.filterset = filters.PsatFilter(data=self.request.GET, request=self.request)

    def get_psat_context(self):
        psat_context = get_paginator_context(self.filterset.qs, self.page_number)
        for psat in psat_context['page_obj']:
            psat.updated_problem_count = sum(1 for prob in psat.problems.all() if prob.question and prob.data)
            psat.image_problem_count = sum(1 for prob in psat.problems.all() if prob.has_image)
        return psat_context


@dataclass(kw_only=True)
class AdminDetailData:
    request: HtmxHttpRequest
    psat: models.Psat

    def __post_init__(self):
        request_data = RequestData(request=self.request)
        psat_data = PsatData(psat=self.psat)
        self.view_type = request_data.view_type
        self.page_number = request_data.page_number
        self.qs_problem = models.Problem.objects.filtered_problem_by_psat(self.psat)
        self.subject_vars = psat_data.subject_vars

    def get_problem_context(self):
        return get_paginator_context(self.qs_problem, self.page_number)

    def get_answer_official_context(self):
        query_dict = defaultdict(list)
        for query in self.qs_problem.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for sub, (_, _, idx, _) in self.subject_vars.items()
        }


@dataclass(kw_only=True)
class AdminCreateData:
    form: forms.PsatForm

    def __post_init__(self):
        self.exam = self.form.cleaned_data['exam']
        self.psat = self.create_psat()

    def create_psat(self):
        psat = self.form.save(commit=False)
        exam_order = {'행시': 1, '입시': 2, '칠급': 3}
        psat.order = exam_order.get(self.exam)
        psat.save()
        return psat

    @with_bulk_create_or_update()
    def process_post_request(self):
        list_create, list_update = [], []

        def append_list(problem_count: int, *subject_list):
            for subject in subject_list:
                for number in range(1, problem_count + 1):
                    problem_info = {'psat': self.psat, 'subject': subject, 'number': number}
                    append_list_create(models.Problem, list_create, **problem_info)

        if self.exam in ['행시', '입시']:
            append_list(40, '언어', '자료', '상황')
            append_list(25, '헌법')
        elif self.exam in ['칠급']:
            append_list(25, '언어', '자료', '상황')

        return models.Problem, list_create, list_update, []


@dataclass(kw_only=True)
class AdminUpdateData:
    request: HtmxHttpRequest
    psat: models.Psat

    def process_post_request(self):
        file = self.request.FILES['file']
        df = pd.read_excel(file, header=0, index_col=0)

        answer_symbol = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
        keys = list(answer_symbol.keys())
        combinations = []
        for i in range(1, 6):
            combinations.extend(itertools.combinations(keys, i))

        replace_dict = {}
        for combination in combinations:
            key = ''.join(combination)
            value = int(''.join(str(answer_symbol[k]) for k in combination))
            replace_dict[key] = value

        df['answer'].replace(to_replace=replace_dict, inplace=True)
        df = df.infer_objects(copy=False)

        for index, row in df.iterrows():
            problem = models.Problem.objects.get(psat=self.psat, subject=row['subject'], number=row['number'])
            problem.paper_type = row['paper_type']
            problem.answer = row['answer']
            problem.question = row['question']
            problem.data = row['data']
            problem.save()


def create_img_wide(img, width, height, threshold_height, img_wide_path):
    target_height = 1500 if height < threshold_height + 500 else height // 2
    split_y = find_split_point(img, target_height)
    img1 = img.crop((0, 0, width, split_y))
    img2 = img.crop((0, split_y, width, height))

    width1, height1 = img1.size
    width2, height2 = img2.size
    new_width = width1 + width2
    new_height = max(height1, height2)

    img_wide = Image.new('RGB', (new_width, new_height), (255, 255, 255))
    img_wide.paste(img1, (0, 0))
    img_wide.paste(img2, (width1, 0))
    img_wide.save(img_wide_path, format='PNG')


def find_split_point(image, target_height=1000, margin=50) -> int:
    """target_height ± margin 내에서 여백(밝은 부분)을 찾아 분할 위치를 반환"""
    width, height = image.size
    crop_area = (0, max(0, target_height - margin), width, min(height, target_height + margin))
    cropped = image.crop(crop_area).convert('L')  # 밝기 기반

    pixels = cropped.load()
    scores = []
    for y in range(cropped.height):
        brightness = sum(pixels[x, y] for x in range(cropped.width))
        scores.append((brightness, y))

    # 밝은 부분 (여백) 우선
    best = max(scores, key=lambda x: x[0])
    split_y = crop_area[1] + best[1]
    return split_y


def get_custom_data(user: User) -> dict:
    def get_filtered_qs(model, *args):
        if not args:
            args = ['user', 'problem']
        qs = model.objects.filter(is_active=True).select_related(*args)

        if model == models.ProblemCollectionItem:
            return qs.filter(collection__user=user)
        return qs.filter(user=user)

    if user and user.is_authenticated:
        return {
            'like': get_filtered_qs(models.ProblemLike),
            'rate': get_filtered_qs(models.ProblemRate),
            'solve': get_filtered_qs(models.ProblemSolve),
            'memo': get_filtered_qs(models.ProblemMemo),
            'tag': get_filtered_qs(models.ProblemTaggedItem, *['user', 'content_object']),
            'collection': get_filtered_qs(models.ProblemCollectionItem, *['collection__user', 'problem']),
        }
    return {
        'like': [], 'rate': [], 'solve': [], 'memo': [], 'tag': [], 'collection': [],
    }


def get_custom_icons(problem: models.Problem, custom_data: dict):
    def get_status(status_type, field=None, default: bool | int | None = False):
        for dt in custom_data[status_type]:
            problem_id = getattr(dt, 'problem_id', getattr(dt, 'content_object_id', ''))
            if problem_id == problem.id:
                default = getattr(dt, field) if field else True
        return default

    is_liked = get_status(status_type='like', field='is_liked')
    rating = get_status(status_type='rate', field='rating', default=0)
    is_correct = get_status(status_type='solve', field='is_correct', default=None)
    is_memoed = get_status('memo')
    is_tagged = get_status('tag')
    is_collected = get_status('collection')

    problem.icon_like = icon_set_new.ICON_LIKE[f'{is_liked}']
    problem.icon_rate = icon_set_new.ICON_RATE[f'star{rating}']
    problem.icon_solve = icon_set_new.ICON_SOLVE[f'{is_correct}']
    problem.icon_memo = icon_set_new.ICON_MEMO[f'{is_memoed}']
    problem.icon_tag = icon_set_new.ICON_TAG[f'{is_tagged}']
    problem.icon_collection = icon_set_new.ICON_COLLECTION[f'{is_collected}']


def get_all_comments(queryset, problem_id=None):
    if problem_id:
        queryset = queryset.filter(problem_id=problem_id)
    parent_comments = queryset.filter(parent__isnull=True).order_by('-created_at')
    child_comments = queryset.exclude(parent__isnull=True).order_by('parent_id', '-created_at')
    all_comments = []
    for comment in parent_comments:
        all_comments.append(comment)
        all_comments.extend(child_comments.filter(parent=comment))
    return all_comments
