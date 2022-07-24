from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredientEntry, ShoppingCart, Subscribe,
                            Tag)
from rest_framework import serializers
from users.models import User

EMPTY_INGREDIENTS_LIST_ERROR = (
    'The recipe should have at least one ingredient!'
)
INGREDIENT_DOES_NOT_EXIST_ERROR = 'Unexisting ingredient.'
AMOUNT_IS_NOT_INTEGER_ERROR = '"amount" must be an integer value.'
AMOUNT_IS_NOT_POSITIVE_ERROR = '"amount" must be a positive integer.'
INGREDIENT_IS_NOT_UNIQUE_ERROR = (
    'There should be only one unique ingredient in the recipe.'
)
NO_TAG_ERROR = 'There should be at least one tag.'
TAG_IS_NOT_UNIQUE_ERROR = 'Tag must be unique.'
COOKING_TIME_VALUE_ERROR = 'Cooking time should be an integer value.'
COOKING_TIME_IS_NOT_POSITIVE = 'Cooking time should be a positive integer.'


class CommonRecipe(metaclass=serializers.SerializerMetaclass):
    is_in_favorites = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_in_favorites(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Favorite.objects.filter(
            user=request.user,
            recipe__id=obj.id
        ).exists():
            return True
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if ShoppingCart.objects.filter(
            user=request.user,
            recipe__id=obj.id
        ).exists():
            return True
        else:
            return False


class CommonCount(metaclass=serializers.SerializerMetaclass):
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        extra_kwargs = {
            'name': {'required': False},
            'slug': {'required': False},
            'color': {'required': False}
        }


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

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measure_unit')
        extra_kwargs = {
            'name': {'required': False},
            'measure_unit': {'required': False}
        }


class RecipeIngredientEntrySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measure_unit = serializers.ReadOnlyField(
        source='ingredient.measure_unit'
    )

    class Meta:
        model = RecipeIngredientEntry
        fields = ('id', 'name', 'measure_unit', 'amount')


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = RecipeIngredientEntry
        fields = ('id', 'amount')


class FavouriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class ShoppingCartSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class RecipeSerializer(serializers.ModelSerializer, CommonRecipe):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientEntrySerializer(
        source='ingredient_entries', many=True
    )
    is_in_favorites = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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
            'is_in_favorites',
            'is_in_shopping_cart',
        )


class RecipeCreateSerializer(serializers.ModelSerializer, CommonRecipe):
    author = UserSerializer(read_only=True)
    image = Base64ImageField(max_length=None, use_url=False,)
    ingredients = IngredientAmountRecipeSerializer(
        source='ingredient_entries',
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    EMPTY_INGREDIENTS_LIST_ERROR
                )
            id_to_check = ingredient['ingredient']['id']
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise serializers.ValidationError(
                    INGREDIENT_DOES_NOT_EXIST_ERROR
                )
            if ingredient_to_check in ingredients_list:
                raise serializers.ValidationError(
                    INGREDIENT_IS_NOT_UNIQUE_ERROR
                )
            ingredients_list.append(ingredient_to_check)
        return value

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
        objs = [
            RecipeIngredientEntry(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredientEntry.objects.bulk_create(objs)

    def create(self, validated_data):
        author = validated_data.get('author')
        tags_data = validated_data.pop('tags')
        name = validated_data.get('name')
        image = validated_data.get('image')
        text = validated_data.get('text')
        cooking_time = validated_data.get('cooking_time')
        ingredients = validated_data.pop('ingredient_entries')
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time,
        )
        self.add_tag(tags_data, recipe)
        self.add_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredient_entries')
        instance.tags.clear()
        instance.ingredients.clear()
        self.add_tag(tags_data, instance)
        self.add_ingredient(ingredients_data, instance)
        super().update(instance, validated_data)
        return instance

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
            'is_in_favorites',
            'is_in_shopping_cart'
        )


class UserSubscriptionSerializer(serializers.ModelSerializer, CommonCount):
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
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
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
