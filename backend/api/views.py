from django.db.models import Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404

from django_filters import rest_framework
from recipes.models import (Favourite, Ingredient, Recipe,
                            RecipeIngredientEntry, ShoppingList, Subscribe,
                            Tag)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsStaffOrOwnerOrReadOnly, IsStaffOrReadOnly
from .serializers import (FavouriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          ShoppingListSerializer, TagSerializer,
                          UserSubscriptionSerializer)

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

    def create(self, request, *args, **kwargs):
        user_id = self.kwargs.get('users_id')
        user = get_object_or_404(User, id=user_id)
        Subscribe.objects.create(
            user=request.user, follows=user
        )
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        user_id = self.kwargs.get('users_id')
        user = get_object_or_404(User, id=user_id)
        Subscribe.objects.filter(
            user=request.user, follows=user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListFollowViewSet(generics.ListAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = UserSubscriptionSerializer

    def get_queryset(self):
        return get_list_or_404(User, follows__user=self.request.user)


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


class BaseFavoriteCartViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]

    def create(self, request, *args, **kwargs):
        recipe_id = int(self.kwargs['recipes_id'])
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if self.model.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            self.model.objects.filter(
                user=request.user, recipe=recipe
            ).delete()
        self.model.objects.create(
            user=request.user, recipe=recipe
        )
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs['recipes_id']
        user_id = request.user.id
        object = get_object_or_404(
            self.model, user__id=user_id, recipe__id=recipe_id
        )
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListViewSet(BaseFavoriteCartViewSet):
    serializer_class = ShoppingListSerializer
    queryset = ShoppingList.objects.all()
    model = ShoppingList


class FavouriteViewSet(BaseFavoriteCartViewSet):
    serializer_class = FavouriteSerializer
    queryset = Favourite.objects.all()
    model = Favourite


class DownloadShoppingList(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request):
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
