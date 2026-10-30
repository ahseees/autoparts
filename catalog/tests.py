
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Favorite, Notification
from .models import CarMake, CarModel, Category, Manufacturer, Part


class CatalogTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.brakes = Category.objects.create(
            name="Тормозная система",
            slug="brakes"
        )
        cls.filters = Category.objects.create(
            name="Фильтры",
            slug="filters"
        )
        cls.maker = Manufacturer.objects.create(name="Bosch")

        toyota = CarMake.objects.create(
            name="Toyota",
            slug="toyota"
        )
        kia = CarMake.objects.create(
            name="Kia",
            slug="kia"
        )

        cls.camry = CarModel.objects.create(
            make=toyota,
            name="Camry",
            year_from=2017,
            year_to=2023
        )
        cls.rio = CarModel.objects.create(
            make=kia,
            name="Rio",
            year_from=2017,
            year_to=2023
        )

        cls.pads = Part.objects.create(
            category=cls.brakes,
            manufacturer=cls.maker,
            name="Тормозные колодки",
            slug="pads",
            sku="T-1",
            price=Decimal("3500"),
            stock=5
        )
        cls.pads.compatible_models.add(cls.camry)

        cls.oil_filter = Part.objects.create(
            category=cls.filters,
            manufacturer=cls.maker,
            name="Масляный фильтр",
            slug="oil-filter",
            sku="T-2",
            price=Decimal("700"),
            stock=0
        )
        cls.oil_filter.compatible_models.add(cls.rio)

        cls.hidden = Part.objects.create(
            category=cls.brakes,
            manufacturer=cls.maker,
            name="Снятая с продажи деталь",
            slug="hidden",
            sku="T-3",
            price=Decimal("100"),
            is_active=False
        )

        User = get_user_model()

        cls.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123!"
        )

    # 1. Неактивные товары скрыты
    def test_inactive_part_is_hidden(self):
        response = self.client.get(reverse("catalog:part_list"))

        self.assertContains(response, self.pads.name)
        self.assertNotContains(response, self.hidden.name)

        response = self.client.get(
            self.hidden.get_absolute_url()
        )
        self.assertEqual(response.status_code, 404)

    # 2. Фильтрация по категории
    def test_category_filter(self):
        response = self.client.get(
            self.filters.get_absolute_url()
        )

        self.assertContains(response, self.oil_filter.name)
        self.assertNotContains(response, self.pads.name)

    # 3. Поиск без учёта регистра
    def test_search_ignores_case(self):
        response = self.client.get(
            reverse("catalog:part_list"),
            {"q": "МАСЛЯНЫЙ"}
        )

        self.assertContains(response, self.oil_filter.name)
        self.assertNotContains(response, self.pads.name)

    # 4. Фильтрация по марке, модели и году
    def test_filter_by_make_model_year(self):
        url = reverse("catalog:part_list")

        response = self.client.get(
            url,
            {
                "make": "toyota",
                "model": "Camry",
                "year": 2020
            }
        )

        self.assertContains(response, self.pads.name)
        self.assertNotContains(response, self.oil_filter.name)

        response = self.client.get(
            url,
            {
                "make": "toyota",
                "model": "Camry",
                "year": 2010
            }
        )

        self.assertNotContains(response, self.pads.name)

    # 5. Пагинация
    def test_pagination(self):
        for number in range(10):
            Part.objects.create(
                category=self.filters,
                manufacturer=self.maker,
                name=f"Фильтр {number}",
                slug=f"filter-{number}",
                sku=f"F-{number}",
                price=Decimal("500")
            )

        response = self.client.get(
            reverse("catalog:part_list"),
            {"page": 2}
        )

        self.assertEqual(
            response.context["page"].number,
            2
        )

        self.assertEqual(
            len(response.context["page"].object_list),
            4
        )

    # 6. Цена должна быть положительной
    def test_price_must_be_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Part.objects.create(
                category=self.brakes,
                manufacturer=self.maker,
                name="Бесплатно",
                slug="free",
                sku="T-9",
                price=Decimal("0")
            )

    # 7. Корректность диапазона годов
    def test_car_years_must_be_valid(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CarModel.objects.create(
                make=self.camry.make,
                name="Тест",
                year_from=2023,
                year_to=2017
            )

    # 8. Главная страница открывается
    def test_catalog_opens(self):
        response = self.client.get(
            reverse("catalog:part_list")
        )

        self.assertEqual(response.status_code, 200)

    # 9. Страница товара открывается
    def test_part_detail_opens(self):
        response = self.client.get(
            self.pads.get_absolute_url()
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pads.name)

    # 10. Поиск по артикулу
    def test_search_by_sku(self):
        response = self.client.get(
            reverse("catalog:part_list"),
            {"q": "T-1"}
        )

        self.assertContains(response, self.pads.name)
        self.assertNotContains(response, self.oil_filter.name)

    # 11. Сортировка по цене
    def test_sort_by_price(self):
        response = self.client.get(
            reverse("catalog:part_list"),
            {"sort": "cheap"}
        )

        parts = list(
            response.context["page"].object_list
        )

        self.assertEqual(parts[0], self.hidden) if False else None
        self.assertEqual(parts[0], self.oil_filter)
        self.assertEqual(parts[1], self.pads)

    # 12. Проверка наличия товара
    def test_stock_status(self):
        self.assertTrue(self.pads.in_stock)
        self.assertFalse(self.oil_filter.in_stock)

    # 13. Добавление в избранное
    def test_favorite_add(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("favorite_toggle", args=[self.pads.pk])
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Favorite.objects.filter(
                user=self.user,
                part=self.pads
            ).exists()
        )

    # 14. Удаление из избранного
    def test_favorite_remove(self):
        Favorite.objects.create(
            user=self.user,
            part=self.pads
        )

        self.client.force_login(self.user)

        self.client.post(
            reverse("favorite_toggle", args=[self.pads.pk])
        )

        self.assertFalse(
            Favorite.objects.filter(
                user=self.user,
                part=self.pads
            ).exists()
        )

    # 15. Избранное требует авторизации
    def test_favorite_requires_login(self):
        response = self.client.post(
            reverse("favorite_toggle", args=[self.pads.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Favorite.objects.exists())

    # 16. Изменять избранное можно только POST
    def test_favorite_only_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("favorite_toggle", args=[self.pads.pk])
        )

        self.assertEqual(response.status_code, 405)

    # 17. Уведомление при поступлении товара
    def test_restock_notification(self):
        Favorite.objects.create(
            user=self.user,
            part=self.oil_filter
        )

        self.oil_filter.stock = 5
        self.oil_filter.save()

        self.assertTrue(
            Notification.objects.filter(
                user=self.user,
                is_read=False
            ).exists()
        )
