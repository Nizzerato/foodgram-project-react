from django_filters import rest_framework
from recipes.models import Recipe
from rest_framework import filters
from users.models import User


class IngredientSearchFilter(filters.SearchFilter):
    search_param = 'name'


class RecipeFilter(rest_framework.FilterSet):
    author = rest_framework.ModelChoiceFilter(queryset=User.objects.all())
    tags = rest_framework.AllValuesMultipleFilter(field_name='tags__slug')
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
