from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredientEntry,
                     ShoppingCart, Subscribe, Tag, TagRecipe)


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    extra = 0


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', )
    empty_value_display = '-empty-'
    list_filter = ('name',)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure_unit')
    search_fields = ('name', )
    empty_value_display = '-empty-'
    list_filter = ('name',)


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'id')
    search_fields = ('user', )
    empty_value_display = '-empty-'
    list_filter = ('user',)


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user', )
    empty_value_display = '-empty-'
    list_filter = ('user',)


class RecipeIngredientEntryInline(admin.TabularInline):
    model = RecipeIngredientEntry
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientEntryInline, TagRecipeInline,)
    list_display = (
        'name',
        'author',
        'cooking_time',
        'id',
        'count_favorite',
        'created')
    search_fields = ('name', 'author', 'tags')
    empty_value_display = '-empty-'
    list_filter = ('name', 'author', 'tags')

    def count_favorite(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'follows')
    search_fields = ('user', )
    empty_value_display = '-empty-'
    list_filter = ('user',)


admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Subscribe, SubscribeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
