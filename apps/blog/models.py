from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Festival(models.Model):
    """Фестиваль — раздел 4.15 плана.

    Обратная связь с постами блога не хранится отдельным полем — все посты
    с festival=<этот фестиваль> и есть список «постов о фестивале»
    (BlogPost.festival, см. ниже), как и советует план.
    """

    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    date_start = models.DateField("дата начала")
    date_end = models.DateField("дата окончания", blank=True, null=True)

    class Meta:
        verbose_name = "фестиваль"
        verbose_name_plural = "фестивали"
        ordering = ["-date_start"]
        permissions = [
            ("can_manage_festivals", "Может управлять фестивалями и их фотографиями"),
        ]

    def __str__(self):
        return self.title


class FestivalPhoto(models.Model):
    """Фото галереи фестиваля."""

    festival = models.ForeignKey(
        Festival, verbose_name="фестиваль", related_name="photos", on_delete=models.CASCADE,
    )
    image = models.ImageField("изображение", upload_to="festivals/")
    caption = models.CharField("подпись", max_length=200, blank=True)

    class Meta:
        verbose_name = "фото фестиваля"
        verbose_name_plural = "фото фестиваля"
        ordering = ["id"]

    def __str__(self):
        return self.caption or f"Фото #{self.pk}"


class BlogPost(models.Model):
    """Пост блога — раздел 1 плана («Блог»), связь с фестивалем из 4.15."""

    title = models.CharField("заголовок", max_length=200)
    slug = models.SlugField("слаг", max_length=220, unique=True, blank=True, allow_unicode=True)
    excerpt = models.TextField(
        "краткое превью", blank=True, help_text="Если пусто — в списке постов показывается начало текста",
    )
    content = models.TextField("текст")
    cover_image = models.ImageField("обложка", upload_to="blog/covers/", blank=True, null=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="автор", related_name="blog_posts", on_delete=models.PROTECT,
    )
    festival = models.ForeignKey(
        Festival, verbose_name="фестиваль", related_name="blog_posts",
        blank=True, null=True, on_delete=models.SET_NULL,
        help_text="Если пост написан о конкретном фестивале",
    )

    is_published = models.BooleanField("опубликован", default=True)
    published_at = models.DateTimeField("опубликован когда", default=timezone.now)

    class Meta:
        verbose_name = "пост блога"
        verbose_name_plural = "посты блога"
        ordering = ["-published_at"]
        permissions = [
            ("can_manage_blog", "Может создавать/редактировать/удалять посты блога"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base = slugify(self.title, allow_unicode=True) or "post"
        slug = base
        n = 1
        while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            n += 1
            slug = f"{base}-{n}"
        return slug
