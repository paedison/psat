__all__ = [
    'NormalListContext', 'NormalDetailContext',
    'NormalUpdateContext', 'NormalAnnotateProblem',
    'AdminDetailContext',
    'AdminCreateContext', 'AdminUpdateContext',
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
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse

from a_psat import forms
from a_psat.utils.variables import get_prev_next_obj, SubjectVariants, OfficialModelData
from common.constants import icon_set_new
from common.models import User
from common.utils import get_paginator_context, HtmxHttpRequest
from common.utils.modify_models_methods import with_bulk_create_or_update, append_list_create

_model = OfficialModelData()


@dataclass(kw_only=True)
class ProblemData:
    request: HtmxHttpRequest
    problem: _model.problem

    def __post_init__(self):
        self._user = self.request.user if self.request.user.is_authenticated else None
        self.base_list_data = _model.problem.objects.base_list(self.problem)

    def get_problem_list_context(self):
        return {
            'list_title': '', 'color': 'primary',
            'list_data': self.get_list_data(self.base_list_data),
        }

    def get_like_list_context(self):
        like_list = _model.problem.objects.like_list(self.problem, self._user)
        return {
            'list_title': '즐겨찾기 추가 문제', 'color': 'danger',
            'list_data': self.get_list_data(like_list),
        }

    def get_rate_list_context(self):
        rate_list = _model.problem.objects.rate_list(self.problem, self._user)
        return {
            'list_title': '난이도 선택 문제', 'color': 'warning',
            'list_data': self.get_list_data(rate_list),
        }

    def get_solve_list_context(self):
        solve_list = _model.problem.objects.solve_list(self.problem, self._user)
        return {
            'list_title': '정답 확인 문제', 'color': 'success',
            'list_data': self.get_list_data(solve_list),
        }

    def get_memo_list_context(self):
        memo_list = _model.problem.objects.memo_list(self.problem, self._user)
        return {
            'list_title': '메모 작성 문제', 'color': 'warning',
            'list_data': self.get_list_data(memo_list),
        }

    def get_tag_list_context(self):
        tag_list = _model.problem.objects.tag_list(self.problem, self._user)
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
class NormalListContext:
    _request: HtmxHttpRequest

    def get_problem_context(self, queryset, page_number=1):
        custom_data = get_custom_data(self._request.user)
        problem_context = get_paginator_context(queryset, page_number)
        if problem_context:
            for problem in problem_context['page_obj']:
                get_custom_icons(problem, custom_data)
            return problem_context

    def get_collections(self):
        if self._request.user.is_authenticated:
            return _model.collection.objects.user_collection(self._request.user)


@dataclass(kw_only=True)
class NormalDetailContext:
    request: HtmxHttpRequest
    problem: _model.problem

    def __post_init__(self):
        self.process_image()
        self.problem_data = ProblemData(request=self.request, problem=self.problem)
        self.prob_prev, self.prob_next = get_prev_next_obj(self.problem.pk, self.problem_data.base_list_data)
        self.custom_data = self.problem_data.get_custom_data()

    def process_image(self):
        img_normal = img_wide = {'alt': 'Preparing Image', 'src': static('image/preparing.png')}
        self.problem.has_img = False
        if self.problem.absolute_img_path.exists():
            img_normal = {'alt': 'Problem Image', 'src': self.problem.relative_img_path}
            img_wide = img_normal.copy()
            self.problem.has_img = True

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
                return _model.memo.objects.user_memo_for_problem(self.request.user, self.problem)

    def get_my_tags(self):
        for dt in self.custom_data['tag']:
            if dt.content_object_id == self.problem.id:
                return _model.tag.objects.user_tags_for_problem(self.request.user, self.problem)
        return []


@dataclass(kw_only=True)
class NormalUpdateContext:
    request: HtmxHttpRequest
    problem: _model.problem

    def get_like_problem_response(self):
        new_record = self.create_new_custom_record(_model.like)
        icon_like = icon_set_new.ICON_LIKE[f'{new_record.is_liked}']
        return HttpResponse(f'{icon_like}')

    def get_rate_problem_response(self, rating):
        _ = self.create_new_custom_record(_model.rate, **{'rating': rating})
        icon_rate = icon_set_new.ICON_RATE[f'star{rating}']
        return HttpResponse(icon_rate)

    def get_solve_problem_response_context(self, answer):
        is_correct = None
        if answer:
            answer = int(answer)
            is_correct = answer == self.problem.answer
            _ = self.create_new_custom_record(_model.solve, **{'answer': answer, 'is_correct': is_correct})
        return {
            'problem': self.problem, 'answer': answer, 'is_correct': is_correct,
            'icon_solve': icon_set_new.ICON_SOLVE[f'{is_correct}'],
        }

    def get_my_memo(self, content):
        return self.create_new_custom_record(_model.memo, **{'content': content})

    def create_new_custom_record(self, model, **kwargs):
        base_info = {'problem': self.problem, 'user': self.request.user, 'is_active': True}
        latest_record = model.objects.filter(**base_info).first()
        if latest_record:
            if isinstance(latest_record, _model.like):
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
        self.lookup_expr = {
            'problem_id': self.pk,
            'user': self.request.user,
            'annotate_type': self.request.GET.get('annotate_type'),
        }

    def process_post_request_to_save_annotation(self):
        problem = get_object_or_404(_model.problem, pk=self.pk)
        data = json.loads(self.request.body)
        image_data = data.get('image')
        fmt, imgstr = image_data.split(';base64,')

        if not image_data.startswith('data:image/png;base64,'):
            return JsonResponse({'success': False, 'error': '이미지 형식이 잘못 설정되었습니다.'})

        try:
            annotation = _model.annotation.objects.get(**self.lookup_expr)
            filename = annotation.image.name.split('/')[-1]
            annotation.image.delete(save=False)
        except _model.annotation.DoesNotExist:
            annotation = _model.annotation.objects.create(**self.lookup_expr)
            ext = fmt.split('/')[-1]
            filename = f'{problem.reference}_{uuid.uuid4()}.{ext}'

        image_file = ContentFile(base64.b64decode(imgstr), name=filename)
        annotation.image.save(filename, image_file, save=True)
        return JsonResponse({'success': True, 'image_url': annotation.image.url})

    def process_get_request_to_load_annotation(self):
        try:
            try:
                annotation = _model.annotation.objects.get(**self.lookup_expr)
                return JsonResponse({'success': True, 'image_url': annotation.image.url})
            except _model.annotation.DoesNotExist:
                return JsonResponse({'success': False})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@dataclass(kw_only=True)
class AdminDetailContext:
    request: HtmxHttpRequest
    psat: _model.psat

    def __post_init__(self):
        self._subject_variants = SubjectVariants(_psat=self.psat)
        self._qs_problem = _model.problem.objects.filtered_problem_by_psat(self.psat)

    def get_problem_context(self):
        page_number = self.request.GET.get('page', 1)
        return get_paginator_context(self._qs_problem, page_number)

    def get_answer_official_context(self):
        sub_list = self._subject_variants.sub_list
        query_dict = defaultdict(list)
        for query in self._qs_problem.order_by('id'):
            query_dict[query.subject].append(query)
        return {
            sub: {'id': str(idx), 'title': sub, 'page_obj': query_dict[sub]}
            for idx, sub in enumerate(sub_list)
        }


@dataclass(kw_only=True)
class AdminCreateContext:
    form: forms.PsatForm

    def __post_init__(self):
        self.exam = self.form.cleaned_data['exam']
        self.psat = self.create_psat()

    def create_psat(self):
        psat = self.form.save(commit=False)
        exam_order = {'행시': 1, '입시': 2, '칠급': 3, '국8': 4}
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
                    append_list_create(_model.problem, list_create, **problem_info)

        if self.exam in ['행시', '입시']:
            append_list(40, '언어', '자료', '상황')
            append_list(25, '헌법')
        elif self.exam in ['칠급']:
            append_list(25, '언어', '자료', '상황')
        elif self.exam in ['국8']:
            append_list(20, '언어', '자료', '상황')

        return _model.problem, list_create, list_update, []


@dataclass(kw_only=True)
class AdminUpdateContext:
    _request: HtmxHttpRequest
    _context: dict

    @with_bulk_create_or_update()
    def process_post_request(self):
        problem_model = _model.problem
        psat = self._context.get('psat')
        replace_dict = self.get_replace_dict()

        file = self._request.FILES['file']
        df = pd.read_excel(file)
        df['answer'] = df['answer'].replace(to_replace=replace_dict)
        df = df.infer_objects(copy=False)
        df.fillna(value={'answer': 1, 'question': '', 'data': ''}, inplace=True)

        qs_problem = problem_model.objects.select_related('psat')
        if psat:
            qs_problem = qs_problem.filter(psat=psat)
        problem_dict = {
            (qs_p.psat.year, qs_p.psat.exam, qs_p.subject, qs_p.number): qs_p for qs_p in qs_problem
        }

        list_update = []
        update_fields = ['paper_type', 'answer', 'question', 'data']
        for index, row in df.iterrows():
            year = row['year']
            exam = row['exam']
            subject = row['subject']
            number = row['number']
            problem = problem_dict.get((year, exam, subject, number))

            update_info = {fld: row[fld] for fld in update_fields}
            if problem:
                fields_not_match = any(getattr(problem, fld) != val for fld, val in update_info.items())
                if fields_not_match:
                    for fld, val in update_info.items():
                        setattr(problem, fld, val)
                    list_update.append(problem)

        return problem_model, [], list_update, update_fields

    @staticmethod
    def get_replace_dict():
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

        return replace_dict


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

        if model == _model.collection_item:
            return qs.filter(collection__user=user)
        return qs.filter(user=user)

    if user and user.is_authenticated:
        return {
            'like': get_filtered_qs(_model.like),
            'rate': get_filtered_qs(_model.rate),
            'solve': get_filtered_qs(_model.solve),
            'memo': get_filtered_qs(_model.memo),
            'tag': get_filtered_qs(_model.tagged, *['user', 'content_object']),
            'collection': get_filtered_qs(_model.collection_item, *['collection__user', 'problem']),
        }
    return {
        'like': [], 'rate': [], 'solve': [], 'memo': [], 'tag': [], 'collection': [],
    }


def get_custom_icons(problem: _model.problem, custom_data: dict):
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
