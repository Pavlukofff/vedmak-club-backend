from django.core import signing
from django.core.files.base import ContentFile
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import read_email_verification_token, send_verification_email
from .models import AvatarPreset, CurrencyTransfer, DisplayNameChangeRequest, User
from .serializers import (
    AvatarPresetSerializer,
    CurrencyTransferSerializer,
    DisplayNameChangeRequestSerializer,
    MeSerializer,
    PublicProfileDetailSerializer,
    PublicProfileSerializer,
    RegisterSerializer,
)


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Логин по JWT с троттлингом попыток входа (раздел 3 плана)."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RegisterView(generics.CreateAPIView):
    """Раздел 4.1 плана. Регистрация не блокируется подтверждением email —
    письмо отправляется, но email_verified остаётся False до перехода по ссылке.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email(user, self.request)


class EmailVerifyView(APIView):
    """GET /api/accounts/verify-email/?token=... — переход по ссылке из письма."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get("token", "")
        try:
            data = read_email_verification_token(token)
        except signing.SignatureExpired:
            return Response({"detail": "Ссылка устарела."}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({"detail": "Недействительная ссылка."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, pk=data["user_id"], email=data["email"])
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        return Response({"detail": "Email подтверждён."})


class MeView(generics.RetrieveUpdateAPIView):
    """Личный кабинет — раздел 4.5 плана."""

    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AvatarPresetListView(generics.ListAPIView):
    """Раздел 4.2 плана: галерея пресетов, доступна всем без условий."""

    queryset = AvatarPreset.objects.filter(is_active=True)
    serializer_class = AvatarPresetSerializer
    permission_classes = [permissions.AllowAny]


class SetAvatarPresetView(APIView):
    """POST {"preset_id": N} — выбор пресет-аватара, доступно сразу после регистрации."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        preset = get_object_or_404(AvatarPreset, pk=request.data.get("preset_id"), is_active=True)
        user = request.user
        user.avatar.save(
            preset.image.name.rsplit("/", 1)[-1],
            ContentFile(preset.image.read()),
            save=True,
        )
        return Response(MeSerializer(user).data)


class UploadAvatarView(APIView):
    """POST multipart {"image": file} — раздел 4.2: только после подтверждения email."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.email_verified:
            return Response(
                {"detail": "Подтвердите email, чтобы загрузить свою аватарку."},
                status=status.HTTP_403_FORBIDDEN,
            )
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "Файл не передан."}, status=status.HTTP_400_BAD_REQUEST)
        request.user.avatar.save(image.name, image, save=True)
        return Response(MeSerializer(request.user).data)


class PublicProfileListView(generics.ListAPIView):
    """Раздел 1 плана: список участников клуба (публичные профили)."""

    queryset = User.objects.filter(is_active=True).select_related("school", "rank")
    serializer_class = PublicProfileSerializer
    permission_classes = [permissions.AllowAny]


class PublicProfileDetailView(generics.RetrieveAPIView):
    queryset = User.objects.filter(is_active=True).select_related("school", "rank")
    serializer_class = PublicProfileDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "username"


def can_review_displayname_requests(user):
    return user.is_authenticated and (
        user.is_superuser or user.has_perm("accounts.can_review_displayname_requests")
    )


class DisplayNameChangeRequestListCreateView(generics.ListCreateAPIView):
    """Раздел 4.5 плана: заявка на смену никнейма, в очередь на рассмотрение.

    Участник видит только свои заявки; роль с can_review_displayname_requests —
    все, с фильтром ?user=<username> (очередь на рассмотрение).
    """

    serializer_class = DisplayNameChangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = DisplayNameChangeRequest.objects.select_related("user", "reviewed_by")
        requester = self.request.user
        if can_review_displayname_requests(requester):
            username = self.request.query_params.get("user")
            return qs.filter(user__username=username) if username else qs
        return qs.filter(user=requester)


class DisplayNameChangeRequestReviewView(APIView):
    """POST /api/accounts/displayname-requests/<id>/approve/ | /reject/.

    Раздел 4.5: рассматривает мастер/админ вручную. При одобрении
    пользователю реально присваивается новое отображаемое имя.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, decision):
        if not can_review_displayname_requests(request.user):
            raise PermissionDenied("Нет права рассматривать заявки на смену никнейма.")

        req = get_object_or_404(DisplayNameChangeRequest, pk=pk)
        if req.status != DisplayNameChangeRequest.Status.PENDING:
            return Response({"detail": "Заявка уже рассмотрена."}, status=status.HTTP_400_BAD_REQUEST)

        req.status = (
            DisplayNameChangeRequest.Status.APPROVED if decision == "approve"
            else DisplayNameChangeRequest.Status.REJECTED
        )
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save(update_fields=["status", "reviewed_by", "reviewed_at"])

        if decision == "approve":
            req.user.display_name = req.requested_name
            req.user.save(update_fields=["display_name"])

        return Response(DisplayNameChangeRequestSerializer(req).data)


class CurrencyTransferListCreateView(generics.ListCreateAPIView):
    """Передача кронов любому пользователю — самообслуживание.

    GET — история переводов текущего пользователя (отправленные и полученные).
    POST — отправить перевод; sender всегда сам пользователь.
    """

    serializer_class = CurrencyTransferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CurrencyTransfer.objects.filter(
            Q(sender=user) | Q(recipient=user),
        ).select_related("sender", "recipient")

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)