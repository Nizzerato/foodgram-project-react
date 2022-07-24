from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        db_index=True,
        max_length=150,
        unique=True,
        verbose_name='Username'
    )
    email = models.EmailField(
        db_index=True,
        max_length=254,
        blank=False,
        unique=True,
        verbose_name='User Email'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Name'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Last Name'
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Subscription'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username', 'password', 'first_name', 'last_name'
    )
