from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Cart, Favorite, Ingredient, IngredientRecipe,
                            Recipe, Subscribe, Tag, TagRecipe)
from rest_framework import serializers
from users.models import User


class CommonSubscribed(metaclass=serializers.SerializerMetaclass):
    """Determing the user's subscription to the author."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        """Process the "is_subscribed" parametr."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Subscribe.objects.filter(
                user=request.user, following__id=obj.id).exists():
            return True
        else:
            return False


class CommonRecipe(metaclass=serializers.SerializerMetaclass):
    """Determining favorite recipes and ingredients in the shopping cart."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        """Process the "is_favorited" parameter."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Favorite.objects.filter(user=request.user,
                                   recipe__id=obj.id).exists():
            return True
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        """Process the "is_in_shopping_cart" parameter."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        if Cart.objects.filter(user=request.user,
                               recipe__id=obj.id).exists():
            return True
        else:
            return False


class CommonCount(metaclass=serializers.SerializerMetaclass):
    """Determining the number of author's recipes."""

    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        """Count the number of author's recipes."""
        return Recipe.objects.filter(author__id=obj.id).count()


class RegistrationSerializer(UserCreateSerializer, CommonSubscribed):
    """Creating serializer of the user model."""

    class Meta:
        """Meta-parameter of serializer of the user model."""

        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed', 'password')
        write_only_fields = ('password',)
        read_only_fields = ('id',)
        extra_kwargs = {'is_subscribed': {'required': False}}

    def to_representation(self, obj):
        """Represent of serializer results."""
        result = super(RegistrationSerializer, self).to_representation(obj)
        result.pop('password', None)
        return result


class IngredientSerializer(serializers.ModelSerializer):
    """Creating serializer of the ingredients model."""

    class Meta:
        """Meta-parameter of serializer of ingredients model."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        extra_kwargs = {'name': {'required': False},
                        'measurement_unit': {'required': False}}


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Creating serializer of the ingredients model in the recipe."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        """Meta-parameter serializer of the ingredients model in the recipe."""

        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountRecipeSerializer(serializers.ModelSerializer):
    """Creating serializer of the ingredients amount."""

    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        """Meta-parameter of serializer of the ingredients amount."""

        model = IngredientRecipe
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Creating serializer of the tags model."""

    class Meta:
        """Meta-parameter of serializer of the tags model."""

        model = Tag
        fields = '__all__'
        extra_kwargs = {'name': {'required': False},
                        'slug': {'required': False},
                        'color': {'required': False}}


class FavoriteSerializer(serializers.Serializer):
    """Creating serializer of favorite recipes."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class CartSerializer(serializers.Serializer):
    """Creating serializer of the cart."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(max_length=None, use_url=False,)


class RecipeSerializer(serializers.ModelSerializer,
                       CommonRecipe):
    """Creating serializer of the recipes model."""

    author = RegistrationSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = IngredientAmountSerializer(
        source='ingredientrecipes',
        many=True)
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Meta-parameter of serializer of the recipes model."""

        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time',
                  'is_in_shopping_cart', 'is_favorited')


class RecipeSerializerPost(serializers.ModelSerializer,
                           CommonRecipe):
    """Creating serializer of the ingredients post model."""

    author = RegistrationSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    ingredients = IngredientAmountRecipeSerializer(
        source='ingredientrecipes', many=True)
    image = Base64ImageField(max_length=None, use_url=False,)

    class Meta:
        """Meta-parameter of serializer of the ingredients post model."""

        model = Recipe
        fields = ('id', 'author', 'name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time',
                  'is_in_shopping_cart', 'is_favorited')

    def validate_ingredients(self, value):
        """Validate ingredients in the recipe."""
        ingredients_list = []
        ingredients = value
        for ingredient in ingredients:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество должно быть равным или больше 1!')
            id_to_check = ingredient['ingredient']['id']
            ingredient_to_check = Ingredient.objects.filter(id=id_to_check)
            if not ingredient_to_check.exists():
                raise serializers.ValidationError(
                    'Данного продукта нет в базе!')
            if ingredient_to_check in ingredients_list:
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте!')
            ingredients_list.append(ingredient_to_check)
        return value

    def add_tags_and_ingredients(self, tags_data, ingredients, recipe):
        """Make general functions of creating and changing recipes."""
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
            recipe.save()
        for ingredient in ingredients:
            if not IngredientRecipe.objects.filter(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe).exists():
                ingredientrecipe = IngredientRecipe.objects.create(
                    ingredient_id=ingredient['ingredient']['id'],
                    recipe=recipe)
                ingredientrecipe.amount = ingredient['amount']
                ingredientrecipe.save()
            else:
                IngredientRecipe.objects.filter(
                    recipe=recipe).delete()
                recipe.delete()
                raise serializers.ValidationError(
                    'Данные продукты повторяются в рецепте!')
        return recipe

    def create(self, validated_data):
        """Create recipes."""
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
        """Update recipes."""
        tags_data = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredientrecipes')
        TagRecipe.objects.filter(recipe=instance).delete()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        instance = self.add_tags_and_ingredients(
            tags_data, ingredients, instance)
        super().update(instance, validated_data)
        instance.save()
        return instance


class RecipeMinifieldSerializer(serializers.ModelSerializer):
    """Creating serializer of simplified display of the recipes model."""

    class Meta:
        """Meta-parameters of simplified display of the recipes model."""

        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscriptionSerializer(serializers.ModelSerializer,
                             CommonSubscribed, CommonCount):
    """Creating serializer of the subscriptions list."""

    recipes = serializers.SerializerMethodField()

    class Meta:
        """Meta-parameters of serializer of the subscriptions list."""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Get recipes of author in depend on the "recipes_limit" parameter."""
        request = self.context.get('request')
        if request.GET.get('recipes_limit'):
            recipes_limit = int(request.GET.get('recipes_limit'))
            queryset = Recipe.objects.filter(author__id=obj.id).order_by('id')[
                :recipes_limit]
        else:
            queryset = Recipe.objects.filter(author__id=obj.id).order_by('id')
        return RecipeMinifieldSerializer(queryset, many=True).data
