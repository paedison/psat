import os
from datetime import time, datetime
from pathlib import Path

from PIL import Image
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import make_aware

from _config.settings.base import BASE_DIR
from a_psat import models
from common.constants import icon_set_new
from common.models import User


def get_paginator_data(target_data, page_number, per_page=10, on_each_side=3, on_ends=1):
    paginator = Paginator(target_data, per_page)
    page_obj = paginator.get_page(page_number)
    page_range = paginator.get_elided_page_range(number=page_number, on_each_side=on_each_side, on_ends=on_ends)
    return page_obj, page_range


def get_psat(pk):
    return get_object_or_404(models.Psat, pk=pk)


def get_predict_psat(psat):
    try:
        return psat.predict_psat
    except ObjectDoesNotExist:
        return None


def get_sub_title_by_psat(exam_year, exam_exam, exam_subject, end_string='기출문제') -> str:
    title_parts = []
    if exam_year:
        title_parts.append(f'{exam_year}년')
        if isinstance(exam_year, str):
            exam_year = int(exam_year)

    if exam_exam:
        exam_dict = {
            '행시': '5급공채/행정고시', '외시': '외교원/외무고시', '칠급': '7급공채',
            '입시': '입법고시', '칠예': '7급공채 예시', '민경': '민간경력', '견습': '견습',
        }
        if not exam_year:
            exam_name = exam_dict[exam_exam]
        else:
            if exam_exam == '행시':
                exam_name = '행정고시' if exam_year < 2011 else '5급공채'
            elif exam_exam == '외시':
                exam_name = '외교원' if exam_year == 2013 else '외무고시'
            elif exam_exam == '칠급':
                exam_name = '7급공채 모의고사' if exam_year == 2020 else '7급공채'
            else:
                exam_name = exam_dict[exam_exam]
        title_parts.append(exam_name)

    if exam_subject:
        subject_dict = {'헌법': '헌법', '언어': '언어논리', '자료': '자료해석', '상황': '상황판단'}
        title_parts.append(subject_dict[exam_subject])

    if not exam_year and not exam_exam and not exam_subject:
        title_parts.append('전체')
    else:
        title_parts.append('전체')
    sub_title = f'{" ".join(title_parts)} {end_string}'
    return sub_title


def get_prev_next_prob(pk, custom_data) -> tuple:
    custom_list = list(custom_data.values_list('id', flat=True))
    prev_prob = next_prob = None
    last_id = len(custom_list) - 1
    try:
        q = custom_list.index(pk)
        if q != 0:
            prev_prob = custom_data[q - 1]
        if q != last_id:
            next_prob = custom_data[q + 1]
        return prev_prob, next_prob
    except ValueError:
        return None, None


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


def create_new_custom_record(request, problem, model, **kwargs):
    base_info = {'problem': problem, 'user': request.user, 'is_active': True}
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


def create_new_collection(request, form):
    my_collection = form.save(commit=False)
    collection_counts = models.ProblemCollection.objects.filter(user=request.user, is_active=True).count()
    my_collection.user = request.user
    my_collection.order = collection_counts + 1
    my_collection.save()


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


def get_lecture_images(lecture):
    target_folder = f'image/lecture/psat/{lecture.get_subject_display()}/{lecture.order}/'
    image_folder_path = BASE_DIR / f'static/{target_folder}'
    images = []
    try:
        files = sorted(os.listdir(image_folder_path))
        for file in files:
            static_path = static(f'{target_folder}/{file}')
            images.append(static_path)
    except FileNotFoundError:
        pass
    return images


def get_memo_custom_data(user: User) -> dict:
    if user.is_authenticated:
        return {
            # 'like': models.ProblemLike.objects.filter(user=user).select_related('user', 'problem'),
            'memo': models.LectureMemo.objects.filter(user=user).select_related('user', 'lecture'),
            'tag': models.LectureTaggedItem.objects.filter(
                user=user, active=True).select_related('user', 'content_object'),
        }
    return {'memo': [], 'tag': []}


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


def get_local_time(target_date, target_time=time(9, 0)):
    if not target_date:
        raise ValidationError("Date is required for timezone conversion.")
    target_datetime = datetime.combine(target_date, target_time)
    return make_aware(target_datetime)


def get_datetime_format(target_datetime):
    if target_datetime:
        return timezone.localtime(target_datetime).strftime('%Y/%m/%d %H:%M')
    return '-'
