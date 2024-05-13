from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.db.models.functions import Concat

from reference.models import Subject


class Lecture(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lectures')
    order = models.SmallIntegerField()
    title = models.CharField(max_length=20)
    sub_title = models.CharField(max_length=50)
    youtube_id = models.CharField(max_length=20, null=True, blank=True)
    content = RichTextUploadingField()

    youtube_url = models.GeneratedField(
        expression=models.Case(
            models.When(youtube_id=None, then=models.Value(None)),
            default=Concat(models.Value('https://youtu.be/'), 'youtube_id'),
            output_field=models.URLField(),
        ),
        output_field=models.URLField(),
        db_persist=False,
    )
    thumbnail_url = models.GeneratedField(
        expression=models.Case(
            models.When(youtube_id=None, then=models.Value(None)),
            default=Concat(models.Value('https://img.youtube.com/vi/'), 'youtube_id', models.Value('/maxresdefault.jpg')),
            output_field=models.URLField(),
        ),
        output_field=models.URLField(),
        db_persist=False,
    )
    embed_src = models.GeneratedField(
        expression=models.Case(
            models.When(youtube_id=None, then=models.Value(None)),
            default=Concat(models.Value('https://www.youtube.com/embed/'), 'youtube_id'),
            output_field=models.URLField(),
        ),
        output_field=models.URLField(),
        db_persist=False,
    )

    def __str__(self):
        return f'[{self.subject}] {self.title} - {self.sub_title}'

    class Meta:
        ordering = ['subject', 'order']
