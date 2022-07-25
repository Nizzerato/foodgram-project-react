from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Subscribe, Tag, TagRecipe)
from rest_framework import serializers
from users.models import User

INGREDIENT_DOES_NOT_EXIST_ERROR = 'Unexisting ingredient.'
AMOUNT_IS_NOT_POSITIVE_ERROR = '"amount" must be a positive integer.'
INGREDIENT_IS_NOT_UNIQUE_ERROR = (
    'There should be only one unique ingredient in the recipe.'
)


class CommonSubscribed(metaclass=serializers.SerializerMetaclass):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            Subscribe.objects.filter(
                user=request.user, following__id=obj.id
            ).exists()
            if not request.user.is_anonymous
            else False
        )


class CommonRecipe(metaclass=serializers.SerializerMetaclass):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            Favorite.objects.filter(
                user=request.user,
                recipe__id=obj.id
            ).exists()
            if not request.user.is_anonymous
            else False
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            Cart.objects.filter(
                user=request.user,
                recipe__id=obj.id
            ).exists()
            if not request.user.is_anonymous
            else False
        )


class CommonCount(metaclass=serializers.SerializerMetaclass):
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author__id=obj.id).count()


class RegistrationSerializer(UserCreateSerializer, CommonSubscribed):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )
        write_only_fields = ('password',)
        read_only_fields = ('id',)
        extra_kwargs = {'is_subscribed': {'required': False}}

    def to_representation(self, obj):
        result = super(RegistrationSerializer, self).to_representation(obj)
        result.pop('password', None)
        return result


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        extra_kwargs = {
            'name': {'required': False},
            'measurement_unit': {'required': False}
        }


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': False},
            'slug': {'required': False},
            'color': {'required': False}
        }


class FavoriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField()


class CartSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField()


class RecipeSerializer(
    serializers.ModelSerializer,
    CommonRecipe
):
    author = RegistrationSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientrecipes',
        many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

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
            'is_in_shopping_cart',
            'is_favorited'
        )

    def get_image(self, obj):
        return obj.image.url


class RecipeSerializerPost(
    serializers.ModelSerializer,
    CommonRecipe
):
    author = RegistrationSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientAmountRecipeSerializer(
        source='ingredientrecipes', many=True
    )
    image = Base64ImageField()

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
            'is_in_shopping_cart',
            'is_favorited'
        )

    def validate_ingredients(self, value):
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    AMOUNT_IS_NOT_POSITIVE_ERROR
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

    def add_tags_and_ingredients(self, tags_data, ingredients, recipe):
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
            recipe.save()
        for ingredient in ingredients:
            if not IngredientRecipe.objects.filter(
                ingredient_id=ingredient['ingredient']['id'],
                recipe=recipe
            ).exists():
                ingredientrecipe = IngredientRecipe.objects.create(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe
                )
                ingredientrecipe.amount = ingredient['amount']
                ingredientrecipe.save()
            else:
                IngredientRecipe.objects.filter(
                    recipe=recipe
                ).delete()
                recipe.delete()
                raise serializers.ValidationError(
                    INGREDIENT_IS_NOT_UNIQUE_ERROR
                )
        return recipe

    def create(self, validated_data):
        author = validated_data.get('author')
        tags_data = validated_data.pop('tags')
        name = validated_data.get('name')
        image = validated_data.get('image')
        text = validated_data.get('text')
        cooking_time = validated_data.get('cooking_time')
        ingredients = validated_data.pop('ingredientrecipes')
        recipe = Recipe.objects.create(
            author=author,
            name=name,
            image=image,
            text=text,
            cooking_time=cooking_time,
        )
        return self.add_tags_and_ingredients(tags_data, ingredients, recipe)

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientrecipes')
        TagRecipe.objects.filter(recipe=instance).delete()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        instance = self.add_tags_and_ingredients(
            tags_data, ingredients, instance
        )
        super().update(instance, validated_data)
        instance.save()
        return instance


class RecipeMinifieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptionSerializer(
    serializers.ModelSerializer,
    CommonSubscribed,
    CommonCount
):
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
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
        return RecipeMinifieldSerializer(queryset, many=True).data
