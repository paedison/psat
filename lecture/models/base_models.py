from django.db import models

from lecture.models import Lecture


class Base(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.IntegerField()
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='%(class)ss')

    class Meta:
        abstract = True
        ordering = ['-id']
