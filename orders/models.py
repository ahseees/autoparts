
from django.conf import settings
from django.db import models

from catalog.models import Part


class Order(models.Model):
    STATUS_CHOICES = [
        ("new", "Новый"),
        ("processing", "В обработке"),
        ("completed", "Выполнен"),
        ("cancelled", "Отменён"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    full_name = models.CharField(
        "ФИО покупателя",
        max_length=200,
    )
    email = models.EmailField("Электронная почта")
    phone = models.CharField("Телефон", max_length=30)
    address = models.TextField("Адрес доставки")

    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
    )

    created_at = models.DateTimeField(
        "Дата заказа",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ №{self.pk}"

    @property
    def total_price(self):
        return sum(
            (item.total_price for item in self.items.all()),
            0,
        )


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.PROTECT,
    )
    price = models.DecimalField(
        "Цена на момент покупки",
        max_digits=12,
        decimal_places=2,
    )
    quantity = models.PositiveIntegerField("Количество")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.part.name} × {self.quantity}"
