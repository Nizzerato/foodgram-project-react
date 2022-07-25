from django.contrib import admin

from users.models import User
from .models import Cart
from .models import Favorite
from .models import Subscribe
from .models import Ingredient
from .models import IngredientRecipe
from .models import Recipe
from .models import Tag
from .models import TagRecipe


class IngredientRecipeInline(admin.TabularInline):
    """Parameters of the ingredients model in a recipe."""

    model = IngredientRecipe
    extra = 0


class TagRecipeInline(admin.TabularInline):
    """Parameters of the tags model of a recipe."""

    model = TagRecipe
    extra = 0


class UserAdmin(admin.ModelAdmin):
    """Parametrs of the user admin zone."""

    list_display = ('username', 'email', 'id')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'
    list_filter = ('username', 'email')


class IngredientAdmin(admin.ModelAdmin):
    """Parametrs of the ingredient admin zone."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name', )
    empty_value_display = '-пусто-'
    list_filter = ('name',)


class TagAdmin(admin.ModelAdmin):
    """Parametrs of the tags admin zone."""

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', )
    empty_value_display = '-пусто-'
    list_filter = ('name',)


class CartAdmin(admin.ModelAdmin):
    """Parametrs of the cart admin zone."""

    list_display = ('user', 'recipe', 'id')
    search_fields = ('user', )
    empty_value_display = '-пусто-'
    list_filter = ('user',)


class FavoriteAdmin(admin.ModelAdmin):
    """Parametrs of the favorite recipes admin zone."""

    list_display = ('user', 'recipe')
    search_fields = ('user', )
    empty_value_display = '-пусто-'
    list_filter = ('user',)


class RecipeAdmin(admin.ModelAdmin):
    """Parametrs of the recipes admin zone."""

    inlines = (IngredientRecipeInline, TagRecipeInline,)
    list_display = ('name', 'author', 'cooking_time',
                    'id', 'count_favorite', 'pub_date')
    search_fields = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'
    list_filter = ('name', 'author', 'tags')

    def count_favorite(self, obj):
        """Count the number of the recipe additions to favorites."""
        return Favorite.objects.filter(recipe=obj).count()
    count_favorite.short_description = 'Число добавлении в избранное'


class SubscribeAdmin(admin.ModelAdmin):
    """Parametrs of the admin zone."""

    list_display = ('user', 'following')
    search_fields = ('user', )
    empty_value_display = '-пусто-'
    list_filter = ('user',)


admin.site.register(Cart, CartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
