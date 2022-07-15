from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DownloadShoppingList, IngredientViewSet, FollowingListViewSet,
    RecipeViewSet, TagViewSet, subscribe
)


router_v1 = DefaultRouter()
router_v1.register(r'ingredients', IngredientViewSet)
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet)


urlpatterns = (
    path('users/subscribtions/', FollowingListViewSet.as_view()),
    path('users/<int:uid>/subscribe/', subscribe),
    path(
        'recipes/download_shopping_list/',
        DownloadShoppingList.as_view(),
        name='download_shopping_list',
    ),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
)
