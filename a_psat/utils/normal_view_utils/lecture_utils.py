import os

from django.templatetags.static import static

from _config.settings.base import BASE_DIR
from a_psat import models
from common.models import User


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


def get_lecture_memo_custom_data(user: User) -> dict:
    if user.is_authenticated:
        return {
            # 'like': models.ProblemLike.objects.filter(user=user).select_related('user', 'problem'),
            'memo': models.LectureMemo.objects.filter(user=user).select_related('user', 'lecture'),
            'tag': models.LectureTaggedItem.objects.filter(
                user=user, active=True).select_related('user', 'content_object'),
        }
    return {'memo': [], 'tag': []}
