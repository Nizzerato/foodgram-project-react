from django.contrib.auth import get_user_model
from django.db import models

from users.models import get_deleted_user, User


class Tag(models.Model):
    name = models.CharField(max_length=30)
    color = models.CharField(max_length=200)
    slug = models.SlugField()

    class Meta:
        ordering = ('id',)
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class MeasureUnit(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Measure Unit'
        verbose_name_plural = 'Measure Units'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    measure_unit = models.ForeignKey(MeasureUnit, on_delete=models.RESTRICT)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        unique_together = ('name', 'measure_unit')

    def __str__(self):
        return self.name


class RecipeIngredientEntry(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.RESTRICT)
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_entries'
    )
    amount = models.PositiveIntegerField()

    class Meta:
        ordering = ('id',)
        verbose_name = 'Recipe Ingredient Entry'
        verbose_name_plural = 'Recipe Ingradient Entries'

    def __str__(self):
        return self.ingredient.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET(get_deleted_user),
        related_name='recipes'
    )
    name = models.CharField(max_length=200)
    image = models.ImageField()
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through='recipes.RecipeIngredientEntry'
    )
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveSmallIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return  self.name

    @property
    def favourites_entries(self):
        return self.in_favourites.count()


class Favourites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favourites',
        verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Favourite'
        verbose_name_plural = 'Favourites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourite'
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.user}'


class ShoppingList(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_list',
        verbose_name='Recipes'
    )

    class Meta:
        verbose_name = 'Shopping List'
        verbose_name_plural = 'Shopping Lists'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='User',
    )
    follows = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows',
        verbose_name='Author'
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'follows'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.follows}'
