from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=30,
        verbose_name='Tag Name'
    )
    color = models.CharField(
        max_length=200,
        verbose_name='Tag Color'
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Tag Slug'
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Ingredient Name'
    )
    measure_unit = models.CharField(
        max_length=30,
        verbose_name='Ingredient Measure Unit'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Recipe Author'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Recipe Name'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Recipe Image'
    )
    text = models.TextField(verbose_name='Recipe Text')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredientEntry',
        related_name='recipes',
        verbose_name='Recipe Ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
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


class RecipeIngredientEntry(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_entries',
        verbose_name='Ingredient'
    )
    recipe = models.ForeignKey(
        Recipe,
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
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Tag',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Теги рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'recipe'],
                name='unique_tagrecipe'
            )
        ]

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.recipe} {self.user}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Recipes'
    )

    class Meta:
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
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
