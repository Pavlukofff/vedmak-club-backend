from rest_framework import generics, permissions

from .models import FAQItem
from .serializers import FAQItemSerializer


class FAQItemListView(generics.ListAPIView):
    """Публичный FAQ. ?category=... — фильтр по категории."""

    serializer_class = FAQItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = FAQItem.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs


class FAQItemDetailView(generics.RetrieveAPIView):
    queryset = FAQItem.objects.filter(is_active=True)
    serializer_class = FAQItemSerializer
    permission_classes = [permissions.AllowAny]
