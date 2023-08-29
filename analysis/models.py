from django.db import models


class CorrectAnswer:
    score_set = dict(sub00=4, sub01=2.5, sub02=2.5, sub03=2.5)
    correct_answer_set = {
        'sub00_01': 4, 'sub00_02': 4, 'sub00_03': 2, 'sub00_04': 1, 'sub00_05': 4,
        'sub00_06': 3, 'sub00_07': 4, 'sub00_08': 3, 'sub00_09': 4, 'sub00_10': 1,
        'sub00_11': 3, 'sub00_12': 2, 'sub00_13': 3, 'sub00_14': 3, 'sub00_15': 1,
        'sub00_16': 1, 'sub00_17': 4, 'sub00_18': 3, 'sub00_19': 2, 'sub00_20': 1,
        'sub00_21': 3, 'sub00_22': 4, 'sub00_23': 2, 'sub00_24': 1, 'sub00_25': 3,
        'sub01_01': 4, 'sub01_02': 5, 'sub01_03': 4, 'sub01_04': 3, 'sub01_05': 5,
        'sub01_06': 1, 'sub01_07': 1, 'sub01_08': 4, 'sub01_09': 3, 'sub01_10': 1,
        'sub01_11': 2, 'sub01_12': 4, 'sub01_13': 5, 'sub01_14': 4, 'sub01_15': 5,
        'sub01_16': 4, 'sub01_17': 3, 'sub01_18': 5, 'sub01_19': 3, 'sub01_20': 2,
        'sub01_21': 5, 'sub01_22': 4, 'sub01_23': 3, 'sub01_24': 3, 'sub01_25': 4,
        'sub01_26': 1, 'sub01_27': 1, 'sub01_28': 1, 'sub01_29': 5, 'sub01_30': 3,
        'sub01_31': 4, 'sub01_32': 5, 'sub01_33': 4, 'sub01_34': 3, 'sub01_35': 4,
        'sub01_36': 1, 'sub01_37': 4, 'sub01_38': 3, 'sub01_39': 5, 'sub01_40': 5,
        'sub02_01': 4, 'sub02_02': 4, 'sub02_03': 1, 'sub02_04': 5, 'sub02_05': 2,
        'sub02_06': 3, 'sub02_07': 2, 'sub02_08': 4, 'sub02_09': 3, 'sub02_10': 4,
        'sub02_11': 5, 'sub02_12': 4, 'sub02_13': 5, 'sub02_14': 4, 'sub02_15': 1,
        'sub02_16': 5, 'sub02_17': 3, 'sub02_18': 3, 'sub02_19': 5, 'sub02_20': 3,
        'sub02_21': 3, 'sub02_22': 2, 'sub02_23': 3, 'sub02_24': 2, 'sub02_25': 1,
        'sub02_26': 2, 'sub02_27': 5, 'sub02_28': 5, 'sub02_29': 4, 'sub02_30': 3,
        'sub02_31': 4, 'sub02_32': 2, 'sub02_33': 5, 'sub02_34': 1, 'sub02_35': 1,
        'sub02_36': 1, 'sub02_37': 1, 'sub02_38': 2, 'sub02_39': 3, 'sub02_40': 1,
        'sub03_01': 1, 'sub03_02': 3, 'sub03_03': 1, 'sub03_04': 5, 'sub03_05': 4,
        'sub03_06': 5, 'sub03_07': 3, 'sub03_08': 4, 'sub03_09': 2, 'sub03_10': 3,
        'sub03_11': 5, 'sub03_12': 5, 'sub03_13': 5, 'sub03_14': 1, 'sub03_15': 4,
        'sub03_16': 4, 'sub03_17': 2, 'sub03_18': 1, 'sub03_19': 2, 'sub03_20': 2,
        'sub03_21': 2, 'sub03_22': 2, 'sub03_23': 3, 'sub03_24': 5, 'sub03_25': 4,
        'sub03_26': 2, 'sub03_27': 1, 'sub03_28': 2, 'sub03_29': 4, 'sub03_30': 4,
        'sub03_31': 3, 'sub03_32': 3, 'sub03_33': 1, 'sub03_34': 5, 'sub03_35': 4,
        'sub03_36': 1, 'sub03_37': 3, 'sub03_38': 4, 'sub03_39': 2, 'sub03_40': 3}


class Data(CorrectAnswer, models.Model):
    DEPARTMENT_CHOICES = [
        ("0", "총계"),
        ("1", "5급공채_기술직"),
        ("2", "5급공채_기타"),
        ("3", "5급공채_일반행정"),
        ("4", "5급공채_재경"),
        ("5", "7급_공채"),
        ("6", "외교관후보자"),
        ("7", "지역인재_7급"),
    ]
    objects = models.Manager()

    id = models.AutoField(primary_key=True)
    copy_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    student_number = models.IntegerField()
    student_name = models.TextField()
    password = models.IntegerField()
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default="일반행정")
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

    class Meta:
        ordering = ['-id']

    def get_sub_result(self, sub_code: str) -> dict:
        result = []
        for key, item in self.correct_answer_set.items():
            if key.startswith(f'sub{sub_code}'):
                result.append('O') if getattr(self, key) == item else result.append('X')
        return result

    def get_sub_score(self, sub_code: str) -> int:
        result = self.get_sub_result(sub_code)
        score = self.score_set[sub_code]
        correct_count = sum(1 for answer in result.values() if answer == "O")
        return score * correct_count

    @property
    def sub00_result(self):
        return self.get_sub_result('00')

    @property
    def sub00_score(self):
        return self.get_sub_score('00')

    @property
    def sub01_result(self):
        return self.get_sub_result('01')

    @property
    def sub01_score(self):
        return self.get_sub_score('01')

    @property
    def sub02_result(self):
        return self.get_sub_result('02')

    @property
    def sub02_score(self):
        return self.get_sub_score('02')

    @property
    def sub03_result(self):
        return self.get_sub_result('03')

    @property
    def sub03_score(self):
        return self.get_sub_score('03')
