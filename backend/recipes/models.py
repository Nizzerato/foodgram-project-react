from django.contrib.auth import get_user_model
from django.db import models

from users.models import get_deleted_user


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
        get_user_model(),
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
