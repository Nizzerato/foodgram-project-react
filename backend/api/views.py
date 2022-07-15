from django.db.models import Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Ingredient, Recipe, Tag
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsStaffOrReadOnly, IsStaffOrOwnerOrReadOnly
from .serializers import (
    IngredientSerializer, RecipeCreateSerializer,
    RecipeSerializer, RecipeShortSerializer,
    TagSerializer, UserSubscriptionSerializer
)


ALREADY_SUBSCRIBED_ERROR = 'You are already subscribed to this author.'
NO_SUBSCRIPTION_ERROR = 'You are not subscribed to this author.'
RECIPE_ALREADY_IN_FAVOURITES_ERROR = 'This recipe is already in favourites.'
RECIPE_NOT_IN_FAVOURITES_ERROR = 'This recipe is not in favourites.'
RECIPE_ALREADY_IN_LIST_ERROR = 'This recipe is already in shopping list.'
RECIPE_NOT_IN_LIST_ERROR = 'This recipe is not in shopping list.'


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    permission_classes = [IsStaffOrReadOnly,]
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.select_related()
    permission_classes = [IsStaffOrReadOnly,]
    serializer_class = IngredientSerializer
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def subscribe(request, uid):
    author = get_object_or_404(User, id=uid)
    user = request.user
    serializer = UserSubscriptionSerializer(
        author,
        context={
            'user': user,
            'request': request,
        },
    )
    following = user.follows.filter(id=author.id).exists()
    if request.method == 'GET':
        if not following:
            user.following.add(author)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED
            )
        return Response(
            ALREADY_SUBSCRIBED_ERROR, status=status.HTTP_400_BAD_REQUEST
        )
    if request.method == 'DELETE':
        if following:
            user.following.remove(author)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            NO_SUBSCRIPTION_ERROR, status=status.HTTP_400_BAD_REQUEST
        )


class FollowingListViewSet(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated,]
    serializer_class = UserSubscriptionSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request, 'user': self.request.user})
        return context

    def get_queryset(self):
        return self.request.user.following.prefetch_related()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.prefetch_related()
    permission_classes = [IsStaffOrOwnerOrReadOnly,]
    filter_backends = (rest_framework.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'delete', 'put', 'patch')

    def get_queryset(self):
        user = self.request.user
        return Recipe.objects.prefetch_related().annotate(
            in_favourites=(
                Exists(user.favourite.filter(id=OuterRef('id')))
                if user.is_authenticated
                else Value(False)
            ),
            in_shopping_list=(
                Exists(user.shopping_list.filter(id=OuterRef('id')))
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

    @action(
        methods=('GET', 'DELETE'),
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/favorites',
        serializer_class=RecipeShortSerializer,
    )
    def favourites(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(self.get_queryset(), pk=recipe_id)
        serializer = self.get_serializer(recipe)
        recipe_in_favourites = user.favourites.filter(id=recipe_id).exists()
        if request.method == 'GET':
            if not recipe_in_favourites:
                user.favourites.add(recipe)
                return Response(
                    serializer.data, status==status.HTTP_201_CREATED
                )
            return Response(
                RECIPE_ALREADY_IN_FAVOURITES_ERROR,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if recipe_in_favourites:
                user.favourites.remove(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                RECIPE_NOT_IN_FAVOURITES_ERROR,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=('GET', 'DELETE'),
        detail=False,
        url_path=r'(?P<recipe_id>\d+)/shopping_list',
        serializer_class=RecipeShortSerializer,
    )
    def shopping_list(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(self.get_queryset(), pk=recipe_id)
        serializer = self.get_serializer(recipe)
        recipe_in_list = user.shopping_list.filter(id=recipe_id).exists()
        if request.method == 'GET':
            if not recipe_in_list:
                user.shopping.list.add(recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            return Response(
                RECIPE_ALREADY_IN_LIST_ERROR,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if recipe_in_list:
                user.shopping_list.remove(recipe)
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                RECIPE_NOT_IN_LIST_ERROR,
                status=status.HTTP_400_BAD_REQUEST
            )


class DownloadShoppingList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        shopping_list = {}
        user = request.user
        ingredients = user.shopping_list.values(
            'ingredient_entries__ingredient__name',
            'ingredient_entries__ingredient__measure_unit__name'
        ).annotate(total=Sum('ingredient_entries__amount'))
        for ingredient in ingredients:
            amount = ingredient['total']
            name = ingredient['ingredient_entries__ingredient__name']
            measure_unit = ingredient[
                'ingredient_entries__ingredient__measure_unit__name'
            ]
            shopping_list[name] = {
                'measure_unit': measure_unit,
                'amount': amount,
            }
        cart = []
        for item in shopping_list:
            cart.append(
                f'{item}    {shopping_list[item]["amount"]}  '
                f'{shopping_list[item]["measure_unit"]}\n'
            )
        response = HttpResponse(cart, 'Content-Type: text/plain')
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        return response
