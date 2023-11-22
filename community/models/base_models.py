from django.db import models


class Base(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.IntegerField()
    content = models.TextField()

    class Meta:
        abstract = True
        ordering = ['-id']
