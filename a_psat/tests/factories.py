import factory
import random
from faker import Faker
from a_psat import models

fake = Faker("ko_KR")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    email = factory.LazyAttribute(lambda _: fake.unique.email())
    username = factory.LazyAttribute(lambda _: fake.user_name())
    password = factory.PostGenerationMethodCall('set_password', 'password123!')


class PsatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Psat


class ProblemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Problem

    psat = factory.SubFactory(PsatFactory)


class PredictPsatFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictPsat

    psat = factory.SubFactory(PsatFactory)
    is_active = True


class PredictCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictCategory


class PredictStatisticsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictStatistics

    psat = factory.SubFactory(PsatFactory)


class PredictStudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictStudent

    psat = factory.SubFactory(PsatFactory)
    category = factory.SubFactory(PredictCategoryFactory)
    user = factory.SubFactory(UserFactory)
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


class PredictRankTotalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictRankTotal

    student = factory.SubFactory(PredictStudentFactory)


class PredictRankCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PredictRankCategory

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
