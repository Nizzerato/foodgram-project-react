from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (DownloadShoppingList, IngredientViewSet, RecipeViewSet,
                    SubscribeViewSet, TagViewSet)

router_v1 = DefaultRouter()
router_v1.register(r'ingredients', IngredientViewSet)
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet)


urlpatterns = (
    path(
        'users/subscribtions/',
        SubscribeViewSet.as_view({'get': 'list'}),
        name='subscriptions'
    ),
    path(
        'users/<int:uid>/subscribe/',
        SubscribeViewSet.as_view({'post': 'create', 'delete': 'delete'}),
        name='subscribe'
    ),
    path(
        'recipes/download_shopping_list/',
        DownloadShoppingList.as_view(),
        name='download_shopping_list',
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
)
