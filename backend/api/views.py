from http import HTTPStatus

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
        return Response(HTTPStatus.CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs['recipes_id']
        user_id = request.user.id
        object = get_object_or_404(
            self.model, user__id=user_id, recipe__id=recipe_id
        )
        object.delete()
        return Response(HTTPStatus.NO_CONTENT)


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

    @staticmethod
    def canvas_method(dictionary):
        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'
        ] = 'attachment; filename = "shopping_cart.pdf"'
        begin_position_x, begin_position_y = 40, 650
        sheet = canvas.Canvas(response, pagesize=A4)
        pdfmetrics.registerFont(
            TTFont('List', 'data/List.ttf')
        )
        sheet.setFont('List', 50)
        sheet.setTitle('Список покупок')
        sheet.drawString(
            begin_position_x,
            begin_position_y + 40, 'Список покупок: '
        )
        sheet.setFont('List', 24)
        for number, item in enumerate(dictionary, start=1):
            if begin_position_y < 100:
                begin_position_y = 700
                sheet.showPage()
                sheet.setFont('List', 24)
            sheet.drawString(
                begin_position_x,
                begin_position_y,
                f'{number}.  {item["ingredient__name"]} - '
                f'{item["ingredient_total"]}'
                f' {item["ingredient__measure_unit"]}'
            )
            begin_position_y -= 30
        sheet.showPage()
        sheet.save()
        return response

    def download(self, request):
        result = RecipeIngredientEntry.objects.filter(
            recipe__in_shopping_list__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measure_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_total=Sum('amount'))
        return self.canvas_method(result)
