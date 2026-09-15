from rest_framework import generics, permissions

from .models import ActivityPrice, Subscription
from .serializers import ActivityPriceSerializer, SubscriptionSerializer


class ActivityPriceListView(generics.ListAPIView):
    """Раздел 4.10 плана: разовые занятия, публичная витрина."""

    queryset = ActivityPrice.objects.filter(is_active=True)
    serializer_class = ActivityPriceSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionListView(generics.ListAPIView):
    """Раздел 4.10 плана: абонементы-билеты, публичная витрина без оплаты."""

    queryset = Subscription.objects.filter(is_active=True).prefetch_related("included_activities")
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionDetailView(generics.RetrieveAPIView):
    queryset = Subscription.objects.prefetch_related("included_activities")
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.AllowAny]