from django_filters import rest_framework as django_filter
from rest_framework import filters
from recipes.models import Recipe
from users.models import User


class RecipeFilters(django_filter.FilterSet):
    """Setting up filters of the recipes model."""

    author = django_filter.ModelChoiceFilter(queryset=User.objects.all())
    tags = django_filter.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = django_filter.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filter.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        """Parametrs of filtres of the recipes model."""

        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, queryset, name, value):
        """Process filtres of the is_favorited parameter."""
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        """Process filtres of the is_in_shopping_cart parameter."""
        if self.request.user.is_authenticated and value:
            return queryset.filter(carts__user=self.request.user)
        return queryset.all()


class IngredientSearchFilter(filters.SearchFilter):
    """Setting up filter of the search ingredient model."""

    search_param = 'name'

