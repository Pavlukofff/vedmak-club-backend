from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BlogPost, Festival, FestivalPhoto
from .serializers import (
    BlogPostSerializer,
    BlogPostWriteSerializer,
    FestivalDetailSerializer,
    FestivalPhotoSerializer,
    FestivalSerializer,
    FestivalWriteSerializer,
)


def can_manage_blog(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("blog.can_manage_blog"))


def can_manage_festivals(user):
    return user.is_authenticated and (user.is_superuser or user.has_perm("blog.can_manage_festivals"))


class BlogPostListCreateView(generics.ListCreateAPIView):
    """Раздел 1 плана: блог. Чтение — всем; неопубликованные посты видны

    только роли с can_manage_blog. ?festival=<id> — посты о фестивале.
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return BlogPostWriteSerializer if self.request.method == "POST" else BlogPostSerializer

    def get_queryset(self):
        qs = BlogPost.objects.select_related("author", "festival")
        if not can_manage_blog(self.request.user):
            qs = qs.filter(is_published=True)
        festival_id = self.request.query_params.get("festival")
        if festival_id:
            qs = qs.filter(festival_id=festival_id)
        return qs

    def perform_create(self, serializer):
        if not can_manage_blog(self.request.user):
            raise PermissionDenied("Нет права вести блог.")
        serializer.save(author=self.request.user)


class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Раздел 1 плана: пост блога, поиск по slug."""

    lookup_field = "slug"
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return BlogPostWriteSerializer if self.request.method in ("PUT", "PATCH") else BlogPostSerializer

    def get_queryset(self):
        qs = BlogPost.objects.select_related("author", "festival")
        if not can_manage_blog(self.request.user):
            qs = qs.filter(is_published=True)
        return qs

    def perform_update(self, serializer):
        if not can_manage_blog(self.request.user):
            raise PermissionDenied("Нет права вести блог.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_manage_blog(self.request.user):
            raise PermissionDenied("Нет права вести блог.")
        instance.delete()


class FestivalListCreateView(generics.ListCreateAPIView):
    """Раздел 4.15 плана: фестивали."""

    queryset = Festival.objects.prefetch_related("photos")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return FestivalWriteSerializer if self.request.method == "POST" else FestivalSerializer

    def perform_create(self, serializer):
        if not can_manage_festivals(self.request.user):
            raise PermissionDenied("Нет права управлять фестивалями.")
        serializer.save()


class FestivalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Фестиваль с галереей и связанными постами блога (обратная связь)."""

    queryset = Festival.objects.prefetch_related("photos", "blog_posts")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return FestivalWriteSerializer if self.request.method in ("PUT", "PATCH") else FestivalDetailSerializer

    def perform_update(self, serializer):
        if not can_manage_festivals(self.request.user):
            raise PermissionDenied("Нет права управлять фестивалями.")
        serializer.save()

    def perform_destroy(self, instance):
        if not can_manage_festivals(self.request.user):
            raise PermissionDenied("Нет права управлять фестивалями.")
        instance.delete()


class FestivalPhotoUploadView(APIView):
    """POST multipart {"image": file, "caption": str} — прикрепить фото к фестивалю."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, festival_id):
        if not can_manage_festivals(request.user):
            raise PermissionDenied("Нет права управлять фестивалями.")
        festival = generics.get_object_or_404(Festival, pk=festival_id)
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "Файл не передан."}, status=400)
        photo = FestivalPhoto.objects.create(
            festival=festival, image=image, caption=request.data.get("caption", ""),
        )
        return Response(FestivalPhotoSerializer(photo).data, status=201)


class FestivalPhotoDeleteView(generics.DestroyAPIView):
    queryset = FestivalPhoto.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        if not can_manage_festivals(self.request.user):
            raise PermissionDenied("Нет права управлять фестивалями.")
        instance.delete()
