from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import CarMake, CarModel, Category, Manufacturer, Part


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brakes = Category.objects.create(name="Тормозная система", slug="brakes")
        cls.filters = Category.objects.create(name="Фильтры", slug="filters")
        cls.maker = Manufacturer.objects.create(name="Bosch")

        toyota = CarMake.objects.create(name="Toyota", slug="toyota")
        kia = CarMake.objects.create(name="Kia", slug="kia")
        cls.camry = CarModel.objects.create(
            make=toyota, name="Camry", year_from=2017, year_to=2023
        )
        cls.rio = CarModel.objects.create(
            make=kia, name="Rio", year_from=2017, year_to=2023
        )

        cls.pads = Part.objects.create(
            category=cls.brakes, manufacturer=cls.maker, name="Тормозные колодки",
            slug="pads", sku="T-1", price=Decimal("3500"), stock=5,
        )
        cls.pads.compatible_models.add(cls.camry)

        cls.oil_filter = Part.objects.create(
            category=cls.filters, manufacturer=cls.maker, name="Масляный фильтр",
            slug="oil-filter", sku="T-2", price=Decimal("700"), stock=0,
        )
        cls.oil_filter.compatible_models.add(cls.rio)

        cls.hidden = Part.objects.create(
            category=cls.brakes, manufacturer=cls.maker, name="Снятая с продажи деталь",
            slug="hidden", sku="T-3", price=Decimal("100"), is_active=False,
        )

    def test_inactive_part_is_hidden(self):
        response = self.client.get(reverse("catalog:part_list"))
        self.assertContains(response, self.pads.name)
        self.assertNotContains(response, self.hidden.name)
        response = self.client.get(self.hidden.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_category_filter(self):
        response = self.client.get(self.filters.get_absolute_url())
        self.assertContains(response, self.oil_filter.name)
        self.assertNotContains(response, self.pads.name)

    def test_search_ignores_case(self):
        response = self.client.get(reverse("catalog:part_list"), {"q": "МАСЛЯНЫЙ"})
        self.assertContains(response, self.oil_filter.name)
        self.assertNotContains(response, self.pads.name)

    def test_filter_by_make_model_year(self):
        url = reverse("catalog:part_list")
        response = self.client.get(url, {"make": "toyota", "model": "Camry", "year": 2020})
        self.assertContains(response, self.pads.name)
        self.assertNotContains(response, self.oil_filter.name)

        response = self.client.get(url, {"make": "toyota", "model": "Camry", "year": 2010})
        self.assertNotContains(response, self.pads.name)

    def test_pagination(self):
        for number in range(10):
            Part.objects.create(
                category=self.filters, manufacturer=self.maker, name=f"Фильтр {number}",
                slug=f"filter-{number}", sku=f"F-{number}", price=Decimal("500"),
            )
        response = self.client.get(reverse("catalog:part_list"), {"page": 2})
        self.assertEqual(response.context["page"].number, 2)
        self.assertEqual(len(response.context["page"].object_list), 4)

    def test_price_must_be_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Part.objects.create(
                category=self.brakes, manufacturer=self.maker, name="Бесплатно",
                slug="free", sku="T-9", price=Decimal("0"),
            )

    def test_car_years_must_be_valid(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CarModel.objects.create(
                make=self.camry.make, name="Тест", year_from=2023, year_to=2017
            )