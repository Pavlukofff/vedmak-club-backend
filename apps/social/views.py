from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import SocialLink
from .serializers import SocialLinkSerializer, SocialLinkWriteSerializer


def can_manage_all_links(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("social.can_manage_social_links"))


def can_edit_link(user, owner_type, owner_id):
    """Раздел 4.16 плана: мастер может вести свою собственную ссылку

    (owner_type=master, owner=он сам) без отдельного права; всё остальное
    (клуб/оружейня/чужие ссылки мастеров) — только can_manage_social_links.
    """
    if can_manage_all_links(user):
        return True
    return (
        user.is_authenticated
        and owner_type == SocialLink.OwnerType.MASTER
        and owner_id == user.id
    )


class SocialLinkListCreateView(generics.ListCreateAPIView):
    """Раздел 1 плана: блок соц-сетей клуба/мастеров/оружейни в подвале сайта.

    ?owner_type=club|master|armory — фильтр по типу владельца.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return SocialLinkWriteSerializer if self.request.method == "POST" else SocialLinkSerializer

    def get_queryset(self):
        qs = SocialLink.objects.select_related("owner")
        owner_type = self.request.query_params.get("owner_type")
        if owner_type:
            qs = qs.filter(owner_type=owner_type)
        return qs

    def perform_create(self, serializer):
        owner_type = serializer.validated_data.get("owner_type")
        owner = serializer.validated_data.get("owner")
        owner_id = owner.id if owner else None
        if not can_edit_link(self.request.user, owner_type, owner_id):
            raise PermissionDenied(
                "Можно вести только собственную ссылку мастера; остальное — только с правом can_manage_social_links.",
            )
        serializer.save()


class SocialLinkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = SocialLink.objects.select_related("owner")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return SocialLinkWriteSerializer if self.request.method in ("PUT", "PATCH") else SocialLinkSerializer

    def _check(self, instance):
        if not can_edit_link(self.request.user, instance.owner_type, instance.owner_id):
            raise PermissionDenied(
                "Можно вести только собственную ссылку мастера; остальное — только с правом can_manage_social_links.",
            )

    def perform_update(self, serializer):
        self._check(serializer.instance)

        new_owner = serializer.validated_data.get("owner", serializer.instance.owner)
        new_owner_type = serializer.validated_data.get("owner_type", serializer.instance.owner_type)
        new_owner_id = new_owner.id if new_owner else None
        if not can_edit_link(self.request.user, new_owner_type, new_owner_id):
            raise PermissionDenied(
                "Нельзя переназначить ссылку на владельца, которым вы не управляете.",
            )

        serializer.save()

    def perform_destroy(self, instance):
        self._check(instance)
        instance.delete()
