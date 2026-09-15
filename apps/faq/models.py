from django.db import models


class FAQItem(models.Model):
    """Вопрос-ответ для страницы FAQ — публичный справочник."""

    question = models.CharField("вопрос", max_length=300)
    answer = models.TextField("ответ")
    category = models.CharField(
        "категория", max_length=100, blank=True,
        help_text="Необязательная группировка, например «Регистрация», «Магазин»",
    )
    order = models.PositiveIntegerField("порядок", default=0)
    is_active = models.BooleanField("активен", default=True)

    class Meta:
        verbose_name = "вопрос FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["category", "order", "id"]

    def __str__(self):
        return self.question
