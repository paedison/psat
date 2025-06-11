import os
from dataclasses import dataclass

from django.templatetags.static import static

from _config.settings.base import BASE_DIR
from a_psat import models
from a_psat.utils.variables import get_prev_next_obj
from common.utils import HtmxHttpRequest


@dataclass(kw_only=True)
class NormalDetailData:
    request: HtmxHttpRequest
    lecture: models.Lecture

    def __post_init__(self):
        self.lecture_list = models.Lecture.objects.order_by_subject_code()
        self.prev_lec, self.next_lec = get_prev_next_obj(self.lecture.pk, self.lecture_list)

    def get_lecture_images(self):
        target_folder = f'image/lecture/psat/{self.lecture.get_subject_display()}/{self.lecture.order}/'
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
