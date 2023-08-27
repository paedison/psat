from django.db import models

from common.models import User


class CorrectAnswer:
    score_set = dict(sub00=4, sub01=2.5, sub02=2.5, sub03=2.5)
    correct_answer_set = dict(
        sub00_01="", sub00_02="", sub00_03="", sub00_04="", sub00_05="",
        sub00_06="", sub00_07="", sub00_08="", sub00_09="", sub00_10="",
        sub00_11="", sub00_12="", sub00_13="", sub00_14="", sub00_15="",
        sub00_16="", sub00_17="", sub00_18="", sub00_19="", sub00_20="",
        sub00_21="", sub00_22="", sub00_23="", sub00_24="", sub00_25="",
        sub01_01="", sub01_02="", sub01_03="", sub01_04="", sub01_05="",
        sub01_06="", sub01_07="", sub01_08="", sub01_09="", sub01_10="",
        sub01_11="", sub01_12="", sub01_13="", sub01_14="", sub01_15="",
        sub01_16="", sub01_17="", sub01_18="", sub01_19="", sub01_20="",
        sub01_21="", sub01_22="", sub01_23="", sub01_24="", sub01_25="",
        sub01_26="", sub01_27="", sub01_28="", sub01_29="", sub01_30="",
        sub01_31="", sub01_32="", sub01_33="", sub01_34="", sub01_35="",
        sub01_36="", sub01_37="", sub01_38="", sub01_39="", sub01_40="",
        sub02_01="", sub02_02="", sub02_03="", sub02_04="", sub02_05="",
        sub02_06="", sub02_07="", sub02_08="", sub02_09="", sub02_10="",
        sub02_11="", sub02_12="", sub02_13="", sub02_14="", sub02_15="",
        sub02_16="", sub02_17="", sub02_18="", sub02_19="", sub02_20="",
        sub02_21="", sub02_22="", sub02_23="", sub02_24="", sub02_25="",
        sub02_26="", sub02_27="", sub02_28="", sub02_29="", sub02_30="",
        sub02_31="", sub02_32="", sub02_33="", sub02_34="", sub02_35="",
        sub02_36="", sub02_37="", sub02_38="", sub02_39="", sub02_40="",
        sub03_01="", sub03_02="", sub03_03="", sub03_04="", sub03_05="",
        sub03_06="", sub03_07="", sub03_08="", sub03_09="", sub03_10="",
        sub03_11="", sub03_12="", sub03_13="", sub03_14="", sub03_15="",
        sub03_16="", sub03_17="", sub03_18="", sub03_19="", sub03_20="",
        sub03_21="", sub03_22="", sub03_23="", sub03_24="", sub03_25="",
        sub03_26="", sub03_27="", sub03_28="", sub03_29="", sub03_30="",
        sub03_31="", sub03_32="", sub03_33="", sub03_34="", sub03_35="",
        sub03_36="", sub03_37="", sub03_38="", sub03_39="", sub03_40="")


class Data(CorrectAnswer, models.Model):
    department_choices = [
        ()
    ]
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    student_number = models.IntegerField(max_length=8)
    student_name = models.TextField()
    password = models.IntegerField(max_length=4)
    department = models.Choices(department_choices)
    is_valid = models.BooleanField(default=True)
    sub00_01 = models.IntegerField(default=0)
    sub00_02 = models.IntegerField(default=0)
    sub00_03 = models.IntegerField(default=0)
    sub00_04 = models.IntegerField(default=0)
    sub00_05 = models.IntegerField(default=0)
    sub00_06 = models.IntegerField(default=0)
    sub00_07 = models.IntegerField(default=0)
    sub00_08 = models.IntegerField(default=0)
    sub00_09 = models.IntegerField(default=0)
    sub00_10 = models.IntegerField(default=0)
    sub00_11 = models.IntegerField(default=0)
    sub00_12 = models.IntegerField(default=0)
    sub00_13 = models.IntegerField(default=0)
    sub00_14 = models.IntegerField(default=0)
    sub00_15 = models.IntegerField(default=0)
    sub00_16 = models.IntegerField(default=0)
    sub00_17 = models.IntegerField(default=0)
    sub00_18 = models.IntegerField(default=0)
    sub00_19 = models.IntegerField(default=0)
    sub00_20 = models.IntegerField(default=0)
    sub00_21 = models.IntegerField(default=0)
    sub00_22 = models.IntegerField(default=0)
    sub00_23 = models.IntegerField(default=0)
    sub00_24 = models.IntegerField(default=0)
    sub00_25 = models.IntegerField(default=0)
    sub01_01 = models.IntegerField(default=0)
    sub01_02 = models.IntegerField(default=0)
    sub01_03 = models.IntegerField(default=0)
    sub01_04 = models.IntegerField(default=0)
    sub01_05 = models.IntegerField(default=0)
    sub01_06 = models.IntegerField(default=0)
    sub01_07 = models.IntegerField(default=0)
    sub01_08 = models.IntegerField(default=0)
    sub01_09 = models.IntegerField(default=0)
    sub01_10 = models.IntegerField(default=0)
    sub01_11 = models.IntegerField(default=0)
    sub01_12 = models.IntegerField(default=0)
    sub01_13 = models.IntegerField(default=0)
    sub01_14 = models.IntegerField(default=0)
    sub01_15 = models.IntegerField(default=0)
    sub01_16 = models.IntegerField(default=0)
    sub01_17 = models.IntegerField(default=0)
    sub01_18 = models.IntegerField(default=0)
    sub01_19 = models.IntegerField(default=0)
    sub01_20 = models.IntegerField(default=0)
    sub01_21 = models.IntegerField(default=0)
    sub01_22 = models.IntegerField(default=0)
    sub01_23 = models.IntegerField(default=0)
    sub01_24 = models.IntegerField(default=0)
    sub01_25 = models.IntegerField(default=0)
    sub01_26 = models.IntegerField(default=0)
    sub01_27 = models.IntegerField(default=0)
    sub01_28 = models.IntegerField(default=0)
    sub01_29 = models.IntegerField(default=0)
    sub01_30 = models.IntegerField(default=0)
    sub01_31 = models.IntegerField(default=0)
    sub01_32 = models.IntegerField(default=0)
    sub01_33 = models.IntegerField(default=0)
    sub01_34 = models.IntegerField(default=0)
    sub01_35 = models.IntegerField(default=0)
    sub01_36 = models.IntegerField(default=0)
    sub01_37 = models.IntegerField(default=0)
    sub01_38 = models.IntegerField(default=0)
    sub01_39 = models.IntegerField(default=0)
    sub01_40 = models.IntegerField(default=0)
    sub02_01 = models.IntegerField(default=0)
    sub02_02 = models.IntegerField(default=0)
    sub02_03 = models.IntegerField(default=0)
    sub02_04 = models.IntegerField(default=0)
    sub02_05 = models.IntegerField(default=0)
    sub02_06 = models.IntegerField(default=0)
    sub02_07 = models.IntegerField(default=0)
    sub02_08 = models.IntegerField(default=0)
    sub02_09 = models.IntegerField(default=0)
    sub02_10 = models.IntegerField(default=0)
    sub02_11 = models.IntegerField(default=0)
    sub02_12 = models.IntegerField(default=0)
    sub02_13 = models.IntegerField(default=0)
    sub02_14 = models.IntegerField(default=0)
    sub02_15 = models.IntegerField(default=0)
    sub02_16 = models.IntegerField(default=0)
    sub02_17 = models.IntegerField(default=0)
    sub02_18 = models.IntegerField(default=0)
    sub02_19 = models.IntegerField(default=0)
    sub02_20 = models.IntegerField(default=0)
    sub02_21 = models.IntegerField(default=0)
    sub02_22 = models.IntegerField(default=0)
    sub02_23 = models.IntegerField(default=0)
    sub02_24 = models.IntegerField(default=0)
    sub02_25 = models.IntegerField(default=0)
    sub02_26 = models.IntegerField(default=0)
    sub02_27 = models.IntegerField(default=0)
    sub02_28 = models.IntegerField(default=0)
    sub02_29 = models.IntegerField(default=0)
    sub02_30 = models.IntegerField(default=0)
    sub02_31 = models.IntegerField(default=0)
    sub02_32 = models.IntegerField(default=0)
    sub02_33 = models.IntegerField(default=0)
    sub02_34 = models.IntegerField(default=0)
    sub02_35 = models.IntegerField(default=0)
    sub02_36 = models.IntegerField(default=0)
    sub02_37 = models.IntegerField(default=0)
    sub02_38 = models.IntegerField(default=0)
    sub02_39 = models.IntegerField(default=0)
    sub02_40 = models.IntegerField(default=0)
    sub03_01 = models.IntegerField(default=0)
    sub03_02 = models.IntegerField(default=0)
    sub03_03 = models.IntegerField(default=0)
    sub03_04 = models.IntegerField(default=0)
    sub03_05 = models.IntegerField(default=0)
    sub03_06 = models.IntegerField(default=0)
    sub03_07 = models.IntegerField(default=0)
    sub03_08 = models.IntegerField(default=0)
    sub03_09 = models.IntegerField(default=0)
    sub03_10 = models.IntegerField(default=0)
    sub03_11 = models.IntegerField(default=0)
    sub03_12 = models.IntegerField(default=0)
    sub03_13 = models.IntegerField(default=0)
    sub03_14 = models.IntegerField(default=0)
    sub03_15 = models.IntegerField(default=0)
    sub03_16 = models.IntegerField(default=0)
    sub03_17 = models.IntegerField(default=0)
    sub03_18 = models.IntegerField(default=0)
    sub03_19 = models.IntegerField(default=0)
    sub03_20 = models.IntegerField(default=0)
    sub03_21 = models.IntegerField(default=0)
    sub03_22 = models.IntegerField(default=0)
    sub03_23 = models.IntegerField(default=0)
    sub03_24 = models.IntegerField(default=0)
    sub03_25 = models.IntegerField(default=0)
    sub03_26 = models.IntegerField(default=0)
    sub03_27 = models.IntegerField(default=0)
    sub03_28 = models.IntegerField(default=0)
    sub03_29 = models.IntegerField(default=0)
    sub03_30 = models.IntegerField(default=0)
    sub03_31 = models.IntegerField(default=0)
    sub03_32 = models.IntegerField(default=0)
    sub03_33 = models.IntegerField(default=0)
    sub03_34 = models.IntegerField(default=0)
    sub03_35 = models.IntegerField(default=0)
    sub03_36 = models.IntegerField(default=0)
    sub03_37 = models.IntegerField(default=0)
    sub03_38 = models.IntegerField(default=0)
    sub03_39 = models.IntegerField(default=0)
    sub03_40 = models.IntegerField(default=0)

    def get_sub_result(self, sub_code: str) -> dict:
        result = {}
        for key, item in self.correct_answer_set.items():
            if key.startswith(f'sub{sub_code}'):
                number = int(key[-2:])
                result[number] = 'O' if getattr(self, key) == item else 'X'
        return result

    def get_sub_score(self, sub_code: str) -> int:
        result = self.get_sub_result(sub_code)
        score = self.score_set[sub_code]
        correct_count = sum(1 for answer in result.values() if answer == "O")
        return score * correct_count

    @property
    def sub00_result(self): return self.get_sub_result('00')
    @property
    def sub00_score(self): return self.get_sub_score('00')

    @property
    def sub01_result(self): return self.get_sub_result('01')
    @property
    def sub01_score(self): return self.get_sub_score('01')

    @property
    def sub02_result(self): return self.get_sub_result('02')
    @property
    def sub02_score(self): return self.get_sub_score('02')

    @property
    def sub03_result(self): return self.get_sub_result('03')
    @property
    def sub03_score(self): return self.get_sub_score('03')
