from django.utils.timezone import now
from django.db import models

from common.models import User


class Calendar(models.Model):
    title = models.CharField("제목", max_length=150)
    description = models.TextField("상세 내용", blank=True)

    def __str__(self):
        return f'캘린더 {self.id}. {self.title}'


class Event(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="사용자 ID",
        db_column="user_id",
        default=1,
    )
    calendar = models.ForeignKey(
        Calendar,
        on_delete=models.CASCADE,
        verbose_name="캘린더",
        default=1,
    )
    title = models.CharField("제목", max_length=150)
    description = models.TextField("상세 내용", blank=True)
    start_date = models.DateField("시작일", default=now)
    start_time = models.TimeField("시작 시각", blank=True, null=True)
    end_time = models.TimeField("종료 시각", blank=True, null=True)
    end_date = models.DateField("종료일", default=now)
    all_day = models.BooleanField("종일", default=True)

    def __str__(self):
        return f'이벤트 {self.id}. {self.title}'

    @property
    def get_html_url(self):
        # url = reverse('schedule:edit', args=(self.id,))
        # return f'<a href="{url}"> {self.title} </a>'
        return f'{self.calendar} - {self.title}'
