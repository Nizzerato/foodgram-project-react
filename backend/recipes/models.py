from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Name'
    )

    measurement_unit = models.CharField(
        max_length=200,
        verbose_name='Measurement Unit'
    )

    class Meta:
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Name'
    )

    color = models.CharField(
        max_length=20,
        verbose_name='Color'
    )

    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Unique Slug'
    )

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.slug


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Author'
    )

    name = models.CharField(
        max_length=200,
        verbose_name='Name'
    )

    image = models.ImageField(
        verbose_name='Image',
        upload_to='recipes/'
    )

    text = models.TextField(verbose_name='Recipe Text')

    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cooking Time'
    )

    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Tag'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ingredients'
    )

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date Created'
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='User'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.recipe}'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='User'
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Author'
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_subscribe'
            )
        ]

    def __str__(self):
        return f'{self.user} {self.following}'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredientrecipes',
        verbose_name='Ingredient'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredientrecipes',
        verbose_name='Recipe'
    )

    amount = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Amount'
    )

    class Meta:
        verbose_name = 'Ingredient in Recipe'
        verbose_name_plural = 'Ingredients in Recipe'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredientrecipe'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Tag'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe'
    )

    class Meta:
        verbose_name = 'Recipe Tag'
        verbose_name_plural = 'Recipe Tags'
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
