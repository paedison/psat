from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self): return self.name


class Base(models.Model):
    abbr = models.CharField(max_length=2)
    name = models.CharField(max_length=20)

    class Meta:
        abstract = True


class Exam(Base):
    # Parent[Base] fields: abbr, name
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='exams')
    label = models.CharField(max_length=20)
    remark = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self): return self.name


class Subject(Base):
    # Parent[Base] fields: abbr, name
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subjects')

    def __str__(self): return self.name


class TestBase(models.Model):
    year = models.IntegerField()
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='%(class)s_exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='%(class)s_exams')

    class Meta:
        abstract = True
        ordering = ['-year', 'id']


class ProblemBase(models.Model):
    number = models.IntegerField()
    answer = models.IntegerField()

    class Meta:
        abstract = True
