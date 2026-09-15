from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Title, TitleAward
from .serializers import TitleAwardCreateSerializer, TitleAwardSerializer, TitleSerializer


def can_grant_titles(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("titles.can_grant_titles"))


class TitleListView(generics.ListAPIView):
    """Каталог титулов — публично."""

    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    permission_classes = [permissions.AllowAny]


class TitleAwardListCreateView(generics.ListCreateAPIView):
    """Раздел «Титулы»: выдача — только admin/can_grant_titles.

    ?user=<username> — все титулы конкретного пользователя (публично).
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return TitleAwardCreateSerializer if self.request.method == "POST" else TitleAwardSerializer

    def get_queryset(self):
        qs = TitleAward.objects.select_related("user", "title", "granted_by")
        username = self.request.query_params.get("user")
        if username:
            qs = qs.filter(user__username=username)
        return qs

    def perform_create(self, serializer):
        if not can_grant_titles(self.request.user):
            raise PermissionDenied("Нет права выдавать титулы.")
        if TitleAward.objects.filter(
            user=serializer.validated_data["user"], title=serializer.validated_data["title"],
        ).exists():
            raise ValidationError("У этого пользователя уже есть такой титул.")
        serializer.save(granted_by=self.request.user)


class TitleAwardDetailView(generics.RetrieveDestroyAPIView):
    """Отозвать титул — только admin/can_grant_titles."""

    queryset = TitleAward.objects.select_related("user", "title", "granted_by")
    serializer_class = TitleAwardSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        if not can_grant_titles(self.request.user):
            raise PermissionDenied("Нет права отзывать титулы.")
        instance._deleted_by = self.request.user
        instance.delete()
