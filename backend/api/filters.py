from django import forms

from django_filters import rest_framework
from recipes.models import Ingredient, Recipe
from users.models import User


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class NonValidatingMultipleChoiceField(forms.MultipleChoiceField):
    def validate(self, value):
        pass


class MultipleFieldFilter(rest_framework.AllValuesMultipleFilter):
    field_class = NonValidatingMultipleChoiceField


class RecipeFilter(rest_framework.FilterSet):
    author = rest_framework.ModelChoiceFilter(queryset=User.objects.all())
    tags = MultipleFieldFilter(field_name='tags__slug')
    is_in_favorites = rest_framework.BooleanFilter(
        method='get_is_in_favorites'
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_favorites', 'is_in_shopping_cart')

    def get_is_in_favorites(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset.all()
