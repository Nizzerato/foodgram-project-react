from rest_framework import serializers

from recipes.models import (
    Ingredient, Recipe, RecipeIngredientEntry,
    Tag, Subscribe, ShoppingList, Favourites
)
from users.models import User


EMPTY_INGREDIENTS_LIST_ERROR = (
    'The recipe should have at least one ingredient!'
)
AMOUNT_IS_NOT_INTEGER_ERROR = '"amount" must be an integer value.'
AMOUNT_IS_NOT_POSITIVE_ERROR = '"amount" must be a positive integer.'
INGREDIENT_IS_NOT_UNIQUE_ERROR = (
    'There should be only one unique ingredient in the recipe.'
)
NO_TAG_ERROR = 'There should be at least one tag.'
TAG_IS_NOT_UNIQUE_ERROR = 'Tag must be unique.'
COOKING_TIME_VALUE_ERROR = 'Cooking time should be an integer value.'
COOKING_TIME_IS_NOT_POSITIVE = 'Cooking time should be a positive integer.'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('name', 'color', 'slug')


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            Subscribe.objects.filter(
                user=user, id=obj.id
            ).exists()
            if not user.is_anonymous
            else False
        )


class IngredientSerializer(serializers.ModelSerializer):
    measure_unit = serializers.CharField(source='measure_unit.name')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measure_unit')
        read_only_fields = ('id', 'name', 'measure_unit')


class RecipeIngredientEntrySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measure_unit = serializers.ReadOnlyField(
        source='ingredient.measure_unit.name'
    )

    class Meta:
        model = RecipeIngredientEntry
        fields = ('id', 'name', 'measure_unit', 'amount')
        read_only_fields = ('name', 'measure_unit')


class RecipeIngredientEntryCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    image = serializers.ImageField()
    ingredients = RecipeIngredientEntrySerializer(
        source='ingredient_entries', many=True
    )
    in_favourites = serializers.SerializerMethodField()
    in_shopping_list = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'in_favourites',
            'in_shopping_list',
        )
        read_only_fields = (
            'id',
            'author',
            'in_favourites',
            'in_shopping_list',
        )

    def get_is_in_favourites(self, obj):
        user = self.context.get('request').user
        return (
            Favourites.objects.filter(
                user=user, id=obj.id
            ).exists()
            if not user.is_anonymous
            else False
        )

    def get_is_in_shopping_list(self, obj):
        user = self.context.get('request').user
        return (
            ShoppingList.objects.filter(
                user=user, id=obj.id
            ).exists()
            if not user.is_anonymous
            else False
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    image = serializers.ImageField()
    ingredients = RecipeIngredientEntryCreateSerializer(
        many=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    def validate(self, data):
        ingredients = self.initial_data.get('ingradients')
        ingredients_id = []
        if len(ingredients) == 0:
            raise serializers.ValidationError(EMPTY_INGREDIENTS_LIST_ERROR)
        for ingredient in ingredients:
            try:
                amount = int(ingredient.get('amount'))
            except:
                raise serializers.ValidationError(AMOUNT_IS_NOT_INTEGER_ERROR)
            if amount <= 0:
                raise serializers.ValidationError(
                    AMOUNT_IS_NOT_POSITIVE_ERROR
                )
            elif ingredient['id'] in ingredients_id:
                raise serializers.ValidationError(
                    INGREDIENT_IS_NOT_UNIQUE_ERROR
                )
            else:
                ingredients_id.append(ingredient['id'])
        return data

    def validate_tags(self, data):
        if not data:
            raise serializers.ValidationError(NO_TAG_ERROR)
        unique_tags = set()
        for tag in data:
            if tag in unique_tags:
                raise serializers.ValidationError(TAG_IS_NOT_UNIQUE_ERROR)
            unique_tags.add(tag)
        return data

    def validate_cooking_time(self, data):
        try:
            cooking_time = int(data)
        except ValueError:
            raise serializers.ValidationError(COOKING_TIME_VALUE_ERROR)
        if cooking_time <= 0:
            raise serializers.ValidationError(COOKING_TIME_IS_NOT_POSITIVE)
        return data

    def add_tag(self, tags, recipe):
        for tag in tags:
            recipe.tags.add(tag)

    def add_ingredient(self, ingredients, recipe):
        for ingredient in ingredients:
            ingredient_entry = ingredient['id']
            amount = ingredient['amount']
            recipe.ingredient_entries.create(
                ingredient=ingredient_entry, amount=amount
            )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.add_tags(tags_data, recipe)
        self.add_ingredient(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.ingredients.clear()
        self.add_tags(tags_data, instance)
        self.add_ingredient(ingredients_data, instance)
        super().update(instance, validated_data)
        return instance

    def get_recipe(self, instance):
        return RecipeSerializer(
            instance, context={'request': self.context.get('request')}
        ).data

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
        )


class UserSubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
        )

    def get_recipes(self, obj):
        request = self.context.get('recipes')
        if request.GET.get('recipes_limit'):
            recipes_limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(
                author__id=obj.id
            ).order_by('id')[:recipes_limit]
        else:
            queryset = Recipe.objects.filter(
                author__id=obj.id
            ).order_by('id')
        return RecipeShortSerializer(queryset, many=True).data
