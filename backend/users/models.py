from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        db_index=True,
        max_length=150,
        unique=True,
        verbose_name='Username',
    )

    email = models.EmailField(
        db_index=True,
        unique=True,
        max_length=254,
        verbose_name='Email',
    )

    first_name = models.CharField(
        max_length=150,
        verbose_name='Name',
    )

    last_name = models.CharField(
        max_length=150,
        verbose_name='Last Name',
    )

    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Subscriptions to User',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    def __str__(self):
        return self.username
