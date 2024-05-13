import os

from django.shortcuts import get_object_or_404
from django.templatetags.static import static

from _config.settings.base import BASE_DIR
from . import base_mixins


class BaseMixin(
    base_mixins.ConstantIconSet,
    base_mixins.DefaultModels,
    base_mixins.DefaultMethods,
):
    @property
    def info(self) -> dict:
        """ Get the meta-info for the current view. """
        return {
            'menu': 'lecture',
        }

    def get_lecture_list(self):
        return self.lecture_model.objects.select_related('subject').all()


class ListViewMixin(BaseMixin):
    pass


class DetailViewMixin(BaseMixin):
    def get_prev_next_lecture(self, lecture) -> dict[str, dict]:
        id_list = list(self.lecture_model.objects.values_list('id', flat=True))
        q = id_list.index(lecture.id)
        last = len(id_list) - 1
        prev_lec = next_lec = None
        if q != last:
            next_lec = get_object_or_404(self.lecture_model, id=id_list[q + 1])
        if q != 0:
            prev_lec = self.lecture_model.objects.get(id=id_list[q - 1])
        return prev_lec, next_lec

    @staticmethod
    def get_lecture_images(lecture):
        target_folder = f'image/lecture/psat/{lecture.subject.name}/{lecture.order}/'
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
