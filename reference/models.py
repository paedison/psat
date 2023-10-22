from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=20)


class Exam(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='exams')
    abbr = models.CharField(max_length=2)
    label = models.CharField(max_length=20)
    name = models.CharField(max_length=20)
    remark = models.CharField(max_length=20, null=True, blank=True)


class Subject(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subjects')
    abbr = models.CharField(max_length=2)
    name = models.CharField(max_length=20)


class PsatExam(models.Model):
    year = models.IntegerField()
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='psat_exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='psat_exams')


class PsatProblem(models.Model):
    exam = models.ForeignKey(PsatExam, on_delete=models.CASCADE, related_name='psat_problems')
    number = models.IntegerField()
    answer = models.IntegerField()
    question = models.TextField()
    data = models.TextField()
