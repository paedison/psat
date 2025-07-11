import factory
import random
from faker import Faker
from a_leet import models

fake = Faker("ko_KR")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    username = factory.LazyAttribute(lambda _: fake.user_name())
    password = factory.PostGenerationMethodCall('set_password', 'password123!')


class LeetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Leet


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Problem

    leet = factory.SubFactory(LeetFactory)
    subject = factory.Iterator(['언어', '추리'])
    number = factory.Sequence(lambda n: n + 1)


class PredictLeetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictLeet

    leet = factory.SubFactory(LeetFactory)
    is_active = True


class PredictStatisticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictStatistics

    leet = factory.SubFactory(LeetFactory)


class PredictStudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictStudent

    user = factory.SubFactory(UserFactory)
    leet = factory.SubFactory(LeetFactory)
    serial = factory.LazyAttribute(lambda _: fake.unique.random_number(digits=4))
    name = factory.LazyAttribute(lambda _: fake.name())
    password = factory.LazyAttribute(lambda _: fake.password())


class PredictAnswerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswer

    student = factory.SubFactory(PredictStudentFactory)
    problem = factory.SubFactory(ProblemFactory)
    answer = factory.LazyAttribute(lambda _: random.randint(1, 5))


class PredictAnswerCountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCount

    problem = factory.SubFactory(ProblemFactory)


class PredictScoreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictScore

    student = factory.SubFactory(PredictStudentFactory)


class PredictRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictRank

    student = factory.SubFactory(PredictStudentFactory)


class PredictRankAspiration1Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictRankAspiration1

    student = factory.SubFactory(PredictStudentFactory)


class PredictRankAspiration2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictRankAspiration2

    student = factory.SubFactory(PredictStudentFactory)


class PredictAnswerCountTopRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCountTopRank

    problem = factory.SubFactory(ProblemFactory)


class PredictAnswerCountMidRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCountMidRank

    problem = factory.SubFactory(ProblemFactory)


class PredictAnswerCountLowRankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictAnswerCountLowRank

    problem = factory.SubFactory(ProblemFactory)
