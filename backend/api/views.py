from django.db.models import Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404

from django_filters import rest_framework
from recipes.models import (Favourite, Ingredient, Recipe, ShoppingList,
                            Subscribe, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsStaffOrOwnerOrReadOnly, IsStaffOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          TagSerializer, UserSubscriptionSerializer)

ALREADY_SUBSCRIBED_ERROR = 'You are already subscribed to this author.'
NO_SUBSCRIPTION_ERROR = 'You are not subscribed to this author.'
RECIPE_ALREADY_IN_LIST_ERROR = 'This recipe is already added.'
RECIPE_NOT_IN_LIST_ERROR = 'This recipe is not yet added.'


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [IsStaffOrReadOnly, ]
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.select_related()
    permission_classes = [IsStaffOrReadOnly, ]
    serializer_class = IngredientSerializer
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class SubscribeViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated, ]

    def get_queryset(self):
        return get_list_or_404(User, follows__user=self.request.user)

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get('users_id')
        user = get_object_or_404(User, id=user_id)
        Subscribe.objects.create(
            user=request.user, follows=user)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        author_id = self.kwargs['users_id']
        user_id = request.user.id
        subscribe = get_object_or_404(
            Subscribe, user__id=user_id, follows__id=author_id)
        subscribe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related()
    permission_classes = [IsStaffOrOwnerOrReadOnly, ]
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'delete', 'put', 'patch')

    def get_queryset(self):
        user = self.request.user
        return Recipe.objects.prefetch_related().annotate(
            is_in_favourites=(
                Exists(Favourite.objects.filter(id=OuterRef('id')))
                if user.is_authenticated
                else Value(False)
            ),
            is_in_shopping_list=(
                Exists(ShoppingList.objects.filter(id=OuterRef('id')))
                if user.is_authenticated
                else Value(False)
            ),
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _create_delete_list_object(self, request, recipe_id, class_object):
        recipe = get_object_or_404(self.get_queryset(), pk=recipe_id)
        serializer = self.get_serializer(recipe)
        recipe_in_list = class_object.objects.filter(id=recipe_id).exists()
        if request.method == 'POST':
            if not recipe_in_list:
                class_object.objects.create(recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                RECIPE_ALREADY_IN_LIST_ERROR,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if recipe_in_list:
                class_object.objects.remove(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            RECIPE_NOT_IN_LIST_ERROR,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=('POST', 'DELETE'),
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorite',
        serializer_class=RecipeShortSerializer,
    )
    def favourites(self, request, recipe_id):
        self._create_delete_list_object(request, recipe_id, Favourite)

    @action(
        methods=('POST', 'DELETE'),
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_cart',
        serializer_class=RecipeShortSerializer,
    )
    def shopping_list(self, request, recipe_id):
        self._create_delete_list_object(request, recipe_id, ShoppingList)


class DownloadShoppingList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self):
        shopping_cart = {}
        ingredients = ShoppingList.objects.values(
            'ingredient_entries__ingredient__name',
            'ingredient_entries__ingredient__measure_unit__name'
        ).annotate(total=Sum('ingredient_entries__amount'))
        for ingredient in ingredients:
            amount = ingredient['total']
            name = ingredient['ingredient_entries__ingredient__name']
            measure_unit = ingredient[
                'ingredient_entries__ingredient__measure_unit__name'
            ]
            shopping_cart[name] = {
                'measure_unit': measure_unit,
                'amount': amount,
            }
        cart = []
        for item in shopping_cart:
            cart.append(
                f'{item}    {shopping_cart[item]["amount"]}  '
                f'{shopping_cart[item]["measure_unit"]}\n'
            )
        response = HttpResponse(cart, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        return response
