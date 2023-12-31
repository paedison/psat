from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("이메일을 입력해주세요.")
        user = self.model(email=self.normalize_email(email), username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(email, username=username, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    objects = UserManager()

    email = models.EmailField('이메일', max_length=255, unique=True)
    username = models.CharField('ID', max_length=150, unique=True)
    joined_at = models.DateTimeField('가입일', auto_now_add=True)
    is_active = models.BooleanField('활동 회원', default=True)
    is_admin = models.BooleanField('운영자 여부', default=False)
    is_staff = models.BooleanField('스탭 여부', default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
