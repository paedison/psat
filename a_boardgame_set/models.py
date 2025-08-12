import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.timezone import now

User = get_user_model()


class Card(models.Model):
    COLOR_CHOICES = [('red', 'Red'), ('green', 'Green'), ('purple', 'Purple')]
    SHAPE_CHOICES = [('oval', 'Oval'), ('squiggle', 'Squiggle'), ('diamond', 'Diamond')]
    COUNT_CHOICES = [(1, 'One'), (2, 'Two'), (3, 'Three')]
    FILL_CHOICES = [('open', 'Open'), ('striped', 'Striped'), ('solid', 'Solid')]

    color = models.CharField(max_length=10, choices=COLOR_CHOICES, verbose_name='색깔')
    shape = models.CharField(max_length=10, choices=SHAPE_CHOICES, verbose_name='모양')
    count = models.IntegerField(choices=COUNT_CHOICES, verbose_name='개수')
    fill = models.CharField(max_length=10, choices=FILL_CHOICES, verbose_name='무늬')

    def __str__(self):
        return ' '.join([
            self.get_color_display(),
            self.get_shape_display(),
            self.get_count_display(),
            self.get_fill_display(),
        ])

    def card_info(self):
        return {
            "id": self.id,
            "shape": self.shape,
            "color": self.color,
            "count": self.count,
            "fill": self.fill,
        }

    class Meta:
        ordering = ['id']


class Session(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name='세션 ID')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boardgame_set_sessions')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='시작 시각')
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name='종료 시각')
    total_time = models.FloatField(default=0.0, verbose_name='총 게임 시간')
    finished = models.BooleanField(default=False, verbose_name='종료 여부')

    score = models.IntegerField(default=0, verbose_name='점수')
    set_attempts = models.IntegerField(default=0, verbose_name='세트 시도 횟수')
    hint_requests = models.IntegerField(default=0, verbose_name='힌트 요청 횟수')
    success_count = models.IntegerField(default=0, verbose_name='성공 횟수')
    failure_count = models.IntegerField(default=0, verbose_name='실패 횟수')

    class Meta:
        ordering = ['created_at']

    def remaining_cards(self):
        return self.sessioncard_set.filter(is_used=False).count()

    def elapsed_time(self):
        time = now() - self.created_at
        return time.total_seconds() * 1000

    def save(self, *args, **kwargs):
        self.set_attempts = self.success_count + self.failure_count
        if self.created_at:
            self.total_time = self.elapsed_time() / 1000
        super().save(*args)


class SessionCard(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False, verbose_name='사용 완료')
    used_at = models.DateTimeField(null=True, blank=True, verbose_name='사용 시각')

    class Meta:
        db_table = 'a_boardgame_set_session_card'
        ordering = ['id']


class SessionEvent(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='기록 시각')
    event_type = models.CharField(max_length=32, verbose_name='이벤트 종류')
    detail = models.JSONField(default=dict, verbose_name='세부 내용')

    class Meta:
        db_table = 'a_boardgame_set_session_event'
        ordering = ['timestamp']
