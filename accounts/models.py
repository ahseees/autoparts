
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь интернет-магазина автозапчастей."""


class GarageCar(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="garage_cars",
        verbose_name="Владелец",
    )

    car_model = models.ForeignKey(
        "catalog.CarModel",
        on_delete=models.PROTECT,
        related_name="garage_cars",
        verbose_name="Модель автомобиля",
    )

    year = models.PositiveSmallIntegerField(
        "Год выпуска"
    )

    created_at = models.DateTimeField(
        "Дата добавления",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "автомобиль в гараже"
        verbose_name_plural = "автомобили в гараже"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "car_model", "year"],
                name="unique_user_garage_car"
            )
        ]

    def __str__(self):
        return (
            f"{self.car_model.make.name} "
            f"{self.car_model.name} ({self.year})"
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )

    part = models.ForeignKey(
        "catalog.Part",
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Запчасть",
    )

    created_at = models.DateTimeField(
        "Дата добавления",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "избранный товар"
        verbose_name_plural = "избранные товары"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "part"],
                name="unique_user_favorite_part",
            )
        ]

    def __str__(self):
        return f"{self.user.username} — {self.part.name}"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
    )

    text = models.CharField(
        "Текст уведомления",
        max_length=255,
    )

    link = models.CharField(
        "Ссылка",
        max_length=500,
        blank=True,
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    is_read = models.BooleanField(
        "Прочитано",
        default=False,
    )

    class Meta:
        verbose_name = "уведомление"
        verbose_name_plural = "уведомления"
        ordering = ["-created_at"]

    def __str__(self):
        return self.text
