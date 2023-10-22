from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self): return self.name


class Exam(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='exams')
    abbr = models.CharField(max_length=2)
    label = models.CharField(max_length=20)
    name = models.CharField(max_length=20)
    remark = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self): return self.name


class Subject(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subjects')
    abbr = models.CharField(max_length=2)
    name = models.CharField(max_length=20)

    def __str__(self): return self.name


class Psat(models.Model):
    year = models.IntegerField()
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='psat_exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='psat_exams')

    def __str__(self): return f'{self.year}{self.exam.abbr}{self.subject.abbr}'


class PsatProblem(models.Model):
    psat = models.ForeignKey(Psat, on_delete=models.CASCADE, related_name='psat_problems')
    number = models.IntegerField()
    answer = models.IntegerField()
    question = models.TextField()
    data = models.TextField()

    def __str__(self): return self.psat.exam

