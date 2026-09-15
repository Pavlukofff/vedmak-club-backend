from rest_framework import serializers

from .models import BlogPost, Festival, FestivalPhoto


class FestivalPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FestivalPhoto
        fields = ["id", "image", "caption"]


class FestivalBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Festival
        fields = ["id", "title"]


class BlogPostSerializer(serializers.ModelSerializer):
    """Чтение — раздел 1 плана («Блог»)."""

    author = serializers.SlugRelatedField(slug_field="username", read_only=True)
    festival = FestivalBriefSerializer(read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "slug", "excerpt", "content", "cover_image",
            "author", "festival", "is_published", "published_at",
        ]


class BlogPostWriteSerializer(serializers.ModelSerializer):
    """Создание/редактирование поста — только can_manage_blog (проверяется во view)."""

    festival = serializers.PrimaryKeyRelatedField(
        queryset=Festival.objects.all(), required=False, allow_null=True,
    )

    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "slug", "excerpt", "content", "cover_image",
            "festival", "is_published", "published_at",
        ]
        read_only_fields = ["slug"]


class FestivalSerializer(serializers.ModelSerializer):
    """Список фестивалей — раздел 4.15 плана."""

    photos = FestivalPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Festival
        fields = ["id", "title", "description", "date_start", "date_end", "photos"]


class FestivalDetailSerializer(FestivalSerializer):
    """Детальная страница — плюс посты блога о фестивале (обратная связь)."""

    blog_posts = serializers.SerializerMethodField()

    class Meta(FestivalSerializer.Meta):
        fields = FestivalSerializer.Meta.fields + ["blog_posts"]

    def get_blog_posts(self, obj):
        posts = obj.blog_posts.filter(is_published=True).order_by("-published_at")
        return BlogPostSerializer(posts, many=True).data


class FestivalWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Festival
        fields = ["id", "title", "description", "date_start", "date_end"]
