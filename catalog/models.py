from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse


class Category(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("Адрес (slug)", max_length=100, unique=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:part_list_by_category", args=[self.slug])


class Manufacturer(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)

    class Meta:
        verbose_name = "производитель"
        verbose_name_plural = "производители"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarMake(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("Адрес (slug)", max_length=100, unique=True)

    class Meta:
        verbose_name = "марка автомобиля"
        verbose_name_plural = "марки автомобилей"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    make = models.ForeignKey(
        CarMake, verbose_name="Марка", on_delete=models.CASCADE, related_name="models"
    )
    name = models.CharField("Модель", max_length=100)
    year_from = models.PositiveSmallIntegerField("Год выпуска с")
    year_to = models.PositiveSmallIntegerField("Год выпуска по")

    class Meta:
        verbose_name = "модель автомобиля"
        verbose_name_plural = "модели автомобилей"
        ordering = ["make__name", "name", "year_from"]
        constraints = [
            models.CheckConstraint(
                condition=Q(year_from__lte=F("year_to")),
                name="carmodel_years_valid",
            ),
            models.UniqueConstraint(
                fields=["make", "name", "year_from"], name="carmodel_unique"
            ),
        ]

    def __str__(self):
        return f"{self.make} {self.name} ({self.year_from}–{self.year_to})"


class Part(models.Model):
    category = models.ForeignKey(
        Category, verbose_name="Категория", on_delete=models.PROTECT, related_name="parts"
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name="Производитель",
        on_delete=models.PROTECT,
        related_name="parts",
    )
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField("Адрес (slug)", max_length=200, unique=True)
    sku = models.CharField("Артикул", max_length=50, unique=True)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField(
        "Цена, ₽",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    stock = models.PositiveIntegerField("Остаток на складе", default=0)
    image = models.ImageField("Фото", upload_to="parts/", blank=True)
    is_active = models.BooleanField("Показывать в каталоге", default=True)
    compatible_models = models.ManyToManyField(
        CarModel,
        verbose_name="Подходит к автомобилям",
        related_name="parts",
        blank=True,
    )
    search_index = models.TextField(editable=False, blank=True)
    created_at = models.DateTimeField("Добавлена", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        verbose_name = "запчасть"
        verbose_name_plural = "запчасти"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gt=0), name="part_price_positive"
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_index = f"{self.name} {self.sku} {self.description}".lower()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:part_detail", args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0