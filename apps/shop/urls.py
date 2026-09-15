from django.urls import path

from . import views

urlpatterns = [
    path("items/", views.ShopItemListView.as_view(), name="shop-item-list"),
    path("items/<int:pk>/", views.ShopItemDetailView.as_view(), name="shop-item-detail"),
    path("effect-types/", views.EffectTypeListView.as_view(), name="effect-type-list"),
    path("purchases/", views.PurchaseListCreateView.as_view(), name="purchase-list-create"),
    path("purchases/<int:pk>/", views.PurchaseDetailView.as_view(), name="purchase-detail"),
]