from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404

from django_filters import rest_framework
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe,
                            RecipeIngredientEntry, ShoppingCart, Subscribe,
                            Tag)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, permissions, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User

from .filters import IngredientSearchFilter, RecipeFilter
from .permissions import IsStaffOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          RegistrationSerializer, ShoppingCartSerializer,
                          TagSerializer, UserSubscriptionSerializer)

ALREADY_SUBSCRIBED_ERROR = 'You are already subscribed to this author.'
NO_SUBSCRIPTION_ERROR = 'You are not subscribed to this author.'
RECIPE_ALREADY_IN_LIST_ERROR = 'This recipe is already added.'
RECIPE_NOT_IN_LIST_ERROR = 'This recipe is not yet added.'


class CreateUserView(UserViewSet):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return User.objects.all()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    permission_classes = [IsStaffOrReadOnly, ]
    serializer_class = IngredientSerializer
    filter_backends = (
        rest_framework.DjangoFilterBackend,
        IngredientSearchFilter
    )
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
        author_id = self.kwargs['users_id']
        user_id = request.user.id
        Subscribe.objects.filter(
            user__id=user_id, follows__id=author_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ListFollowViewSet(generics.ListAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = UserSubscriptionSerializer

    def get_queryset(self):
        return get_list_or_404(User, follows__user=self.request.user)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, ]
    filter_class = RecipeFilter
    filter_backends = (rest_framework.DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeCreateSerializer

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


class ShoppingCartViewSet(BaseFavoriteCartViewSet):
    serializer_class = ShoppingCartSerializer
    queryset = ShoppingCart.objects.all()
    model = ShoppingCart


class FavoriteViewSet(BaseFavoriteCartViewSet):
    serializer_class = FavoriteSerializer
    queryset = Favorite.objects.all()
    model = Favorite


class DownloadShoppingCart(APIView):
    permission_classes = [IsAuthenticated, ]

    @staticmethod
    def canvas_method(dictionary):
        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'
        ] = 'attachment; filename = "shopping_cart.pdf"'
        begin_position_x, begin_position_y = 40, 650
        sheet = canvas.Canvas(response, pagesize=A4)
        pdfmetrics.registerFont(TTFont('List', 'data/List.ttf'))
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

    def get(self, request):
        result = RecipeIngredientEntry.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measure_unit'
        ).order_by(
            'ingredient__name'
        ).annotate(ingredient_total=Sum('amount'))
        return self.canvas_method(result)
