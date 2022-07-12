from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


def get_deleted_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]


class User(AbstractUser):
    shopping_list = models.ManyToManyField(
        'recipes.Recipe',
        related_name='in_shopping_list',
        blank=True,
    )
    favourites = models.ManyToManyField(
        'recipes.Recipe',
        related_name='in_favourites',
        blank=True,
    )
    follows = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'login', 'password', 'first_name', 'last_name'
    )
