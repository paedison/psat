import os

from django.db import models
from django.templatetags.static import static
from django.urls import reverse_lazy

from _config.settings.base import BASE_DIR
from .base_models import TestBase, ProblemBase


class Psat(TestBase):
    # Parent[TestBase] fields: year, exam, subject

    def __str__(self): return f'{self.year}{self.exam.abbr}{self.subject.abbr}'


class PsatProblem(ProblemBase):
    # Parent[ProblemBase] fields: number, answer
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='psat_problems')
    question = models.TextField()
    data = models.TextField()

    url_name = 'psat:detail'

    class Meta:
        ordering = ['-psat__year', 'id']

    def __str__(self):
        return f'{self.psat.year}{self.psat.exam.abbr}{self.psat.subject.abbr}-{self.number:02}'

    def get_url(self, view_type: str):
        return reverse_lazy(
            self.url_name,
            kwargs={'view_type': view_type, 'problem_id': self.id}
        )

    def get_problem_url(self):
        return self.get_url('problem')

    def get_like_url(self):
        return self.get_url('like')

    def get_rate_url(self):
        return self.get_url('rate')

    def get_solve_url(self):
        return self.get_url('solve')

    def get_image_file(self) -> dict:
        year, ex, sub = self.psat.year, self.psat.exam.abbr, self.psat.subject.abbr
        year_ex_sub = f'{year}{ex}{sub}'
        number = f'{self.number:02}'
        static_path = BASE_DIR / 'static'

        preparing_image = static('image/preparing.png')
        file1 = f'PSAT{year_ex_sub}{number}-1.png'
        file2 = f'PSAT{year_ex_sub}{number}-2.png'
        problem_image1 = static(f'image/PSAT/{year}/{file1}')
        problem_image2 = static(f'image/PSAT/{year}/{file2}')

        image1_os_path = os.path.join(static_path, 'image', 'PSAT', str(year), file1)
        image1_exists = os.path.exists(image1_os_path)
        image2_os_path = os.path.join(static_path, 'image', 'PSAT', str(year), file2)
        image2_exists = os.path.exists(image2_os_path)

        image_file = {
            'name1': problem_image1 if image1_exists else preparing_image,
            'tag1': 'Problem Image 1' if image1_exists else 'Preparing Image',
            'name2': problem_image2 if image2_exists else '',
            'tag2': 'Problem Image 2' if image2_exists else '',
        }
        return image_file

    @property
    def full_title(self) -> str:
        year = self.psat.year
        exam = self.psat.exam.name
        subject = self.psat.subject.name
        number = self.number
        return f"{year}년 '{exam}' {subject} {number}번"
