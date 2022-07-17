from django.contrib import admin

from .models import Ingredient, MeasureUnit, Recipe, RecipeIngredientEntry, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(MeasureUnit)
class MeasureUnitAdmin(admin.ModelAdmin):
    pass


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'measure_unit')


@admin.register(RecipeIngredientEntry)
class RecipeIngredientEntryAdmin(admin.ModelAdmin):
    pass


class RecipeIngredientEntryInLine(admin.TabularInline):
    model = RecipeIngredientEntry
    list_display = ('ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = (
        ('author', 'favourites_entries'),
        'name',
        'tags',
        'image',
        'text',
        'cooking_time',
    )
    inlines = (RecipeIngredientEntryInLine,)
    readonly_fields = ('favourites_entries',)
    list_display = ('name', 'author')
    list_filter = ('author__username', 'name', 'tags')
