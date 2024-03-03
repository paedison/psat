from rest_framework import serializers
from .models import (
    Student, Answer, AnswerCount, Statistics, StatisticsVirtual
)


class CustomStringField(serializers.CharField):
    def to_representation(self, value):
        if value is None:
            return ''  # Replace None with an empty string
        return super().to_representation(value)


class PredictStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'


class PredictAnswerSerializer(serializers.ModelSerializer):
    prob1 = CustomStringField()
    prob2 = CustomStringField()
    prob3 = CustomStringField()
    prob4 = CustomStringField()
    prob5 = CustomStringField()
    prob6 = CustomStringField()
    prob7 = CustomStringField()
    prob8 = CustomStringField()
    prob9 = CustomStringField()
    prob10 = CustomStringField()
    prob11 = CustomStringField()
    prob12 = CustomStringField()
    prob13 = CustomStringField()
    prob14 = CustomStringField()
    prob15 = CustomStringField()
    prob16 = CustomStringField()
    prob17 = CustomStringField()
    prob18 = CustomStringField()
    prob19 = CustomStringField()
    prob20 = CustomStringField()
    prob21 = CustomStringField()
    prob22 = CustomStringField()
    prob23 = CustomStringField()
    prob24 = CustomStringField()
    prob25 = CustomStringField()
    prob26 = CustomStringField()
    prob27 = CustomStringField()
    prob28 = CustomStringField()
    prob29 = CustomStringField()
    prob30 = CustomStringField()
    prob31 = CustomStringField()
    prob32 = CustomStringField()
    prob33 = CustomStringField()
    prob34 = CustomStringField()
    prob35 = CustomStringField()
    prob36 = CustomStringField()
    prob37 = CustomStringField()
    prob38 = CustomStringField()
    prob39 = CustomStringField()
    prob40 = CustomStringField()

    class Meta:
        model = Answer
        fields = '__all__'


class PredictAnswerCountSerializer(serializers.ModelSerializer):
    answer = CustomStringField()

    class Meta:
        model = AnswerCount
        fields = '__all__'


class PredictStatisticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Statistics
        fields = '__all__'


class PredictStatisticsVirtualSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatisticsVirtual
        fields = '__all__'
