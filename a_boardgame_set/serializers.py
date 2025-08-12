from django.utils.timezone import now
from rest_framework import serializers
from . import models


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Card
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    elapsed_time = serializers.SerializerMethodField()

    class Meta:
        model = models.Session
        fields = [
            'id', 'elapsed_time', 'score', 'hint_requests', 'failure_count', 'success_count',
        ]

    def get_elapsed_time(self, obj):
        time = now() - obj.created_at
        return time.total_seconds() * 1000
