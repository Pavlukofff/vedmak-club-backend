from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import EffectType, Purchase, ShopItem
from .serializers import (
    EffectTypeSerializer,
    PurchaseCreateSerializer,
    PurchaseSerializer,
    PurchaseUpdateSerializer,
    ShopItemSerializer,
)


def can_grant_items(user):
    return user.is_superuser or user.has_perm("shop.can_grant_items")


class ShopItemListView(generics.ListAPIView):
    """Витрина магазина — раздел 4.8 плана.

    ?category=general|potion|scroll — фильтр по категории (обычные/зелья/свитки).
    """

    serializer_class = ShopItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = ShopItem.objects.filter(is_active=True).select_related("min_rank").prefetch_related(
            "effects__type",
        )
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs


class ShopItemDetailView(generics.RetrieveAPIView):
    queryset = ShopItem.objects.select_related("min_rank").prefetch_related("effects__type")
    serializer_class = ShopItemSerializer
    permission_classes = [permissions.AllowAny]


class EffectTypeListView(generics.ListAPIView):
    """Справочник типов эффектов — публично, для отображения расшифровок."""

    queryset = EffectType.objects.all()
    serializer_class = EffectTypeSerializer
    permission_classes = [permissions.AllowAny]


class PurchaseListCreateView(generics.ListCreateAPIView):
    """«Мои покупки / инвентарь» (раздел 1 плана — не расписано в 4.x).

    GET: участник видит только свои покупки; роль с can_grant_items — все,
    с фильтром ?user=<username>.
    POST: самостоятельная покупка за кроны (нужна цена, баланс, наличие)
    либо ручная выдача от can_grant_items (другому пользователю или товару
    без фиксированной цены — без оплаты).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return PurchaseCreateSerializer if self.request.method == "POST" else PurchaseSerializer

    def get_queryset(self):
        qs = Purchase.objects.select_related("user", "item", "granted_by")
        requester = self.request.user
        if can_grant_items(requester):
            username = self.request.query_params.get("user")
            return qs.filter(user__username=username) if username else qs
        return qs.filter(user=requester)

    def perform_create(self, serializer):
        requester = self.request.user
        item = serializer.validated_data["item"]
        target_user = serializer.validated_data.get("user")
        is_grantor = can_grant_items(requester)

        if target_user and target_user != requester and not is_grantor:
            raise PermissionDenied("Можно купить товар только для себя.")
        target_user = target_user or requester

        is_grant = is_grantor and (target_user != requester or item.price is None)

        if item.stock is not None and item.stock <= 0:
            raise ValidationError("Товара нет в наличии.")

        if not is_grant:
            if item.price is None:
                raise ValidationError(
                    "У этого товара нет фиксированной цены — обратитесь к мастеру-алхимику.",
                )
            if target_user.balance < item.price:
                raise ValidationError("Недостаточно кронов.")

        serializer.save(
            user=target_user,
            price_paid=None if is_grant else item.price,
            granted_by=requester if is_grant else None,
        )


class PurchaseDetailView(generics.RetrieveUpdateAPIView):
    """GET — владелец или can_grant_items. PATCH — отметить использованным."""

    queryset = Purchase.objects.select_related("user", "item", "granted_by")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return PurchaseUpdateSerializer if self.request.method in ("PUT", "PATCH") else PurchaseSerializer

    def get_object(self):
        obj = super().get_object()
        requester = self.request.user
        if obj.user_id != requester.id and not can_grant_items(requester):
            raise PermissionDenied("Это не ваша покупка.")
        return obj

    def perform_update(self, serializer):
        if serializer.instance.is_used:
            raise ValidationError("Эта покупка уже отмечена как использованная.")
        if serializer.validated_data.get("is_used"):
            serializer.save(used_at=timezone.now())
        else:
            serializer.save()