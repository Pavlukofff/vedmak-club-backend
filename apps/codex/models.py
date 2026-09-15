from django.conf import settings
from django.db import models


class ClubCodex(models.Model):
    """Кодекс цеха — раздел 1 плана («правила и устав клуба, загружен вами»).

    Текст уже есть (из присланного Word-документа) — здесь только хранилище
    и точка редактирования, без собственной схемы в разделе 4 плана.
    Синглтон-модель, как и SiteSettings в apps.accounts.
    """

    content = models.TextField("текст кодекса", blank=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="кто обновил",
        related_name="+", blank=True, null=True, on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "кодекс цеха"
        verbose_name_plural = "кодекс цеха"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Кодекс цеха"
