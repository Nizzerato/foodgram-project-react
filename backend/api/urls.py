from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (DownloadShoppingList, FavouriteViewSet, IngredientViewSet,
                    ListFollowViewSet, ListRecipesInCartViewSet, RecipeViewSet,
                    ShoppingListViewSet, SubscribeViewSet, TagViewSet)

router_v1 = DefaultRouter()
router_v1.register(
    r'ingredients', IngredientViewSet, basename='ingredients'
)
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet, basename='tags')


urlpatterns = (
    path(
        'users/subscriptions/',
        ListFollowViewSet.as_view()
    ),
    path(
        'users/<int:users_id>/subscribe/',
        SubscribeViewSet.as_view({'post': 'create', 'delete': 'delete'}),
        name='subscribe'
    ),
    path(
        'recipes/download_shopping_cart/',
        DownloadShoppingList.as_view(),
        name='download',
    ),
    path(
        'cart/',
        ListRecipesInCartViewSet.as_view(),
        name='cart',
    ),
    path(
        'recipes/<recipes_id>/favorite/',
        FavouriteViewSet.as_view(
            {'post': 'create', 'delete': 'delete'}
        ), name='favorite'
    ),
    path(
        'recipes/<recipes_id>/shopping_cart/',
        ShoppingListViewSet.as_view(
            {'post': 'create', 'delete': 'delete'}
        ), name='shopping_cart'
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
)
