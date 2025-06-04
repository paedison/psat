from pathlib import Path

from PIL import Image
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from a_psat import models
from common.constants import icon_set_new
from common.models import User
from common.utils import get_paginator_context
from common.utils.decorators import *


@for_normal_views
def get_prev_next_obj(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_obj = next_obj = None
    last_id = len(custom_list) - 1
    try:
        q = custom_list.index(pk)
        if q != 0:
            prev_obj = custom_data[q - 1]
        if q != last_id:
            next_obj = custom_data[q + 1]
        return prev_obj, next_obj
    except ValueError:
        return None, None


@for_normal_views
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


@for_normal_views
def process_image(problem):
    if not problem.absolute_img_path.exists():
        problem.img_normal = problem.img_wide = {'alt': 'Preparing Image', 'src': static('image/preparing.png')}
    else:
        problem.img_normal = {'alt': 'Problem Image', 'src': static(problem.static_img_path)}
        img_wide = {'alt': 'Problem Image', 'src': static(problem.static_img_path)}

        threshold_height = 2000
        img = Image.open(problem.absolute_img_path)
        width, height = img.size
        if height > threshold_height:
            temp_dir = settings.MEDIA_ROOT / 'temp_images'
            Path.mkdir(temp_dir, exist_ok=True)
            img_wide_filename = f'{problem.img_name}_wide.png'
            img_wide_path = temp_dir / img_wide_filename

            if not img_wide_path.exists():
                create_img_wide(img, width, height, threshold_height, img_wide_path)
            img_wide['src'] = f'{settings.MEDIA_URL}temp_images/{img_wide_filename}'

        problem.img_wide = img_wide


@for_normal_views
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


@for_normal_views
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


@for_normal_views
def get_custom_data(user: User) -> dict:
    def get_filtered_qs(model, *args):
        if not args:
            args = ['user', 'problem']
        qs = model.objects.filter(is_active=True).select_related(*args)

        if model == models.ProblemCollectionItem:
            return qs.filter(collection__user=user)
        return qs.filter(user=user)

    if user.is_authenticated:
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


@for_normal_views
def get_problem_context(user, queryset, page_number=1):
    custom_data = get_custom_data(user)
    problem_context = get_paginator_context(queryset, page_number)
    if problem_context:
        for problem in problem_context['page_obj']:
            get_custom_icons(problem, custom_data)
        return problem_context


@for_normal_views
def get_custom_icons(problem, custom_data: dict):
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


@for_normal_views
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


@for_admin_views
def update_official_problem_count(page_obj):
    for psat in page_obj:
        psat.updated_problem_count = sum(1 for prob in psat.problems.all() if prob.question and prob.data)
        psat.image_problem_count = sum(1 for prob in psat.problems.all() if prob.has_image)
