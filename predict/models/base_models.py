from django.db import models


class TimeRecordField(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserIdField(models.Model):
    user_id = models.IntegerField()

    class Meta:
        abstract = True


class NameField(models.Model):
    name = models.CharField(max_length=20)

    class Meta:
        abstract = True


class StudentBase(TimeRecordField, UserIdField):
    year = models.IntegerField()
    serial = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        abstract = True


class AnswerBase(TimeRecordField, UserIdField):
    answer = models.IntegerField("제출 답안")

    class Meta:
        abstract = True


class AnswerCountBase(TimeRecordField):

    @staticmethod
    def rate_dict(ans_number):
        from django.db.models import F
        return {
            'expression': F(f'count_{ans_number}') * 100 / F('count_total'),
            'output_field': models.FloatField(),
            'db_persist': False,
        }

    count_0 = models.IntegerField(default=0)
    count_1 = models.IntegerField(default=0)
    count_2 = models.IntegerField(default=0)
    count_3 = models.IntegerField(default=0)
    count_4 = models.IntegerField(default=0)
    count_5 = models.IntegerField(default=0)
    count_total = models.IntegerField(default=1)
    rate_0 = models.GeneratedField(**rate_dict(0))
    rate_1 = models.GeneratedField(**rate_dict(1))
    rate_2 = models.GeneratedField(**rate_dict(2))
    rate_3 = models.GeneratedField(**rate_dict(3))
    rate_4 = models.GeneratedField(**rate_dict(4))
    rate_5 = models.GeneratedField(**rate_dict(5))
    rate_None = models.IntegerField(default=0)

    class Meta:
        abstract = True


class StatisticsBase(TimeRecordField):
    score_heonbeob = models.FloatField(null=True, blank=True)
    score_eoneo = models.FloatField(null=True, blank=True)
    score_jaryo = models.FloatField(null=True, blank=True)
    score_sanghwang = models.FloatField(null=True, blank=True)
    score_psat = models.FloatField(null=True, blank=True)
    score_psat_avg = models.FloatField(null=True, blank=True)

    rank_total_heonbeob = models.PositiveIntegerField(null=True, blank=True)
    rank_total_eoneo = models.PositiveIntegerField(null=True, blank=True)
    rank_total_jaryo = models.PositiveIntegerField(null=True, blank=True)
    rank_total_sanghwang = models.PositiveIntegerField(null=True, blank=True)
    rank_total_psat = models.PositiveIntegerField(null=True, blank=True)

    rank_department_heonbeob = models.PositiveIntegerField(null=True, blank=True)
    rank_department_eoneo = models.PositiveIntegerField(null=True, blank=True)
    rank_department_jaryo = models.PositiveIntegerField(null=True, blank=True)
    rank_department_sanghwang = models.PositiveIntegerField(null=True, blank=True)
    rank_department_psat = models.PositiveIntegerField(null=True, blank=True)

    rank_ratio_total_heonbeob = models.FloatField(null=True, blank=True)
    rank_ratio_total_eoneo = models.FloatField(null=True, blank=True)
    rank_ratio_total_jaryo = models.FloatField(null=True, blank=True)
    rank_ratio_total_sanghwang = models.FloatField(null=True, blank=True)
    rank_ratio_total_psat = models.FloatField(null=True, blank=True)

    rank_ratio_department_heonbeob = models.FloatField(null=True, blank=True)
    rank_ratio_department_eoneo = models.FloatField(null=True, blank=True)
    rank_ratio_department_jaryo = models.FloatField(null=True, blank=True)
    rank_ratio_department_sanghwang = models.FloatField(null=True, blank=True)
    rank_ratio_department_psat = models.FloatField(null=True, blank=True)

    class Meta:
        abstract = True
