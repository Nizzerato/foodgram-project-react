from django import forms
from django_filters import rest_framework
from recipes.models import Ingredient, Recipe


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
    tags = MultipleFieldFilter(field_name='tags__slug')
    in_favourites = rest_framework.BooleanFilter(method='get_is_in_favourites')
    in_shopping_list = rest_framework.BooleanFilter(
        method='get_is_in_shopping_list'
    )

    def get_is_in_favourites(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(in_favourites=self.request.user)
        return queryset

    def get_is_in_shopping_list(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(in_shopping_list=self.request.user)
        return queryset.all()

    class Meta:
        model = Recipe
        fields = ('tags', 'author')
