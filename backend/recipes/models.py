from django.db import models

from users.models import User, get_deleted_user


class Tag(models.Model):
    name = models.CharField(
        max_length=30,
        verbose_name='Tag Name'
    )
    color = models.CharField(
        max_length=200,
        verbose_name='Tag Color'
    )
    slug = models.SlugField(verbose_name='Tag Slug')

    class Meta:
        ordering = ('id',)
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class MeasureUnit(models.Model):
    name = models.CharField(
        max_length=10,
        verbose_name='Measure Unit Name'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Measure Unit'
        verbose_name_plural = 'Measure Units'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Ingredient Name'
    )
    measure_unit = models.ForeignKey(
        MeasureUnit,
        on_delete=models.RESTRICT,
        verbose_name='Ingredient Measure Unit'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        unique_together = ('name', 'measure_unit')

    def __str__(self):
        return self.name


class RecipeIngredientEntry(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.RESTRICT,
        verbose_name='Ingredient'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='ingredient_entries',
        verbose_name='Recipe'
    )
    amount = models.PositiveIntegerField(verbose_name='Ingredient Amount')

    class Meta:
        ordering = ('id',)
        verbose_name = 'Recipe Ingredient Entry'
        verbose_name_plural = 'Recipe Ingredient Entries'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipeingrediententry'
            )
        ]

    def __str__(self):
        return self.ingredient.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET(get_deleted_user),
        related_name='recipes',
        verbose_name='Recipe Author'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Recipe Name'
    )
    image = models.ImageField(verbose_name='Recipe Image')
    text = models.TextField(verbose_name='Recipe Text')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='recipes.RecipeIngredientEntry',
        verbose_name='Recipe Ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Recipe Tags'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Recipe Cooking Time'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Recipe Creation Date'
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.name

    @property
    def favourites_entries(self):
        return self.in_favourites.count()


class Favourite(models.Model):
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
