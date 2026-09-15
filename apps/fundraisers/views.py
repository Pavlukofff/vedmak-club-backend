from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Fundraiser
from .serializers import (
    ContributionCreateSerializer,
    ContributionSerializer,
    FundraiserDetailSerializer,
    FundraiserSerializer,
    FundraiserWriteSerializer,
)


def can_manage_fundraisers(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("fundraisers.can_manage_fundraisers"))


class FundraiserListCreateView(generics.ListCreateAPIView):
    """Раздел 1 плана: сборы средств (список активных и завершённых, прогресс-бар)."""

    queryset = Fundraiser.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return FundraiserWriteSerializer if self.request.method == "POST" else FundraiserSerializer

    def perform_create(self, serializer):
        if not can_manage_fundraisers(self.request.user):
            raise PermissionDenied("Нет права управлять сборами средств.")
        serializer.save()


class FundraiserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Fundraiser.objects.prefetch_related("contributions__contributor")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return FundraiserWriteSerializer if self.request.method in ("PUT", "PATCH") else FundraiserDetailSerializer

    def perform_update(self, serializer):
        if not can_manage_fundraisers(self.request.user):
            raise PermissionDenied("Нет права управлять сборами средств.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_manage_fundraisers(self.request.user):
            raise PermissionDenied("Нет права управлять сборами средств.")
        instance.delete()


class ContributionCreateView(generics.CreateAPIView):
    """POST — зафиксировать офлайн-взнос. Только can_manage_fundraisers,

    без самозаявления донатера (как и с боями/убийствами монстров).
    """

    serializer_class = ContributionCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not can_manage_fundraisers(self.request.user):
            raise PermissionDenied("Нет права фиксировать взносы.")
        fundraiser = generics.get_object_or_404(Fundraiser, pk=self.kwargs["fundraiser_id"])
        serializer.save(fundraiser=fundraiser, recorded_by=self.request.user)
