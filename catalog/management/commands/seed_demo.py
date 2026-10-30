from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import CarMake, CarModel, Category, Manufacturer, Part

BRAKES = "Тормозная система"
FILTERS = "Фильтры"
FLUIDS = "Масла и жидкости"
SUSPENSION = "Подвеска"
ELECTRICS = "Электрика и зажигание"

CATEGORIES = [
    (BRAKES, "brakes"),
    (FILTERS, "filters"),
    (FLUIDS, "fluids"),
    (SUSPENSION, "suspension"),
    (ELECTRICS, "electrics"),
]

MANUFACTURERS = ["Bosch", "Mann-Filter", "Brembo", "Castrol", "Sachs", "NGK"]

# (марка, slug марки): [(модель, год с, год по), ...]
CARS = {
    ("Toyota", "toyota"): [("Camry", 2017, 2023), ("Corolla", 2013, 2018), ("RAV4", 2013, 2019)],
    ("Kia", "kia"): [("Rio", 2017, 2023), ("Ceed", 2018, 2023)],
    ("Hyundai", "hyundai"): [("Solaris", 2017, 2023), ("Creta", 2016, 2021)],
    ("Volkswagen", "volkswagen"): [("Polo", 2015, 2020), ("Tiguan", 2016, 2023)],
    ("Lada", "lada"): [("Vesta", 2015, 2024), ("Granta", 2011, 2024)],
}

# Группы моделей для краткой записи совместимости
TOYOTA = ["Camry", "Corolla", "RAV4"]
KIA_HYUNDAI = ["Rio", "Ceed", "Solaris", "Creta"]
VW = ["Polo", "Tiguan"]
LADA = ["Vesta", "Granta"]
ALL = None  # None = подходит ко всем моделям

# (название, slug, артикул, категория, производитель, цена, остаток, совместимость)
PARTS = [
    ("Тормозные колодки передние Bosch", "brake-pads-front-bosch", "AP-0001", BRAKES, "Bosch", "3500", 10, TOYOTA),
    ("Тормозные колодки задние Bosch", "brake-pads-rear-bosch", "AP-0002", BRAKES, "Bosch", "2900", 8, ["Camry", "Corolla"]),
    ("Тормозной диск передний Brembo", "brake-disc-front-brembo", "AP-0003", BRAKES, "Brembo", "5400", 6, ["Camry", "RAV4"]),
    ("Тормозной диск задний Brembo", "brake-disc-rear-brembo", "AP-0004", BRAKES, "Brembo", "4200", 0, ["Camry", "RAV4"]),
    ("Тормозные колодки передние Bosch для Kia и Hyundai", "brake-pads-front-kia-hyundai", "AP-0005", BRAKES, "Bosch", "3100", 14, KIA_HYUNDAI),
    ("Тормозные колодки передние Brembo для Volkswagen", "brake-pads-front-vw", "AP-0006", BRAKES, "Brembo", "4800", 5, VW),
    ("Масляный фильтр Mann для Toyota", "oil-filter-toyota", "AP-0007", FILTERS, "Mann-Filter", "750", 30, TOYOTA),
    ("Масляный фильтр Mann для Kia и Hyundai", "oil-filter-kia-hyundai", "AP-0008", FILTERS, "Mann-Filter", "690", 25, KIA_HYUNDAI),
    ("Масляный фильтр Mann для Volkswagen", "oil-filter-vw", "AP-0009", FILTERS, "Mann-Filter", "720", 22, VW),
    ("Масляный фильтр Mann для Lada", "oil-filter-lada", "AP-0010", FILTERS, "Mann-Filter", "480", 50, LADA),
    ("Воздушный фильтр Mann для Toyota", "air-filter-toyota", "AP-0011", FILTERS, "Mann-Filter", "1250", 12, TOYOTA),
    ("Воздушный фильтр Mann для Kia и Hyundai", "air-filter-kia-hyundai", "AP-0012", FILTERS, "Mann-Filter", "980", 16, KIA_HYUNDAI),
    ("Салонный фильтр Mann угольный", "cabin-filter-carbon", "AP-0013", FILTERS, "Mann-Filter", "1100", 18, TOYOTA + VW),
    ("Моторное масло Castrol 5W-30, 4 л", "engine-oil-5w30", "AP-0014", FLUIDS, "Castrol", "4200", 35, ALL),
    ("Моторное масло Castrol 5W-40, 4 л", "engine-oil-5w40", "AP-0015", FLUIDS, "Castrol", "4600", 20, KIA_HYUNDAI + VW + LADA),
    ("Антифриз Castrol, 5 л", "coolant-5l", "AP-0016", FLUIDS, "Castrol", "1350", 28, ALL),
    ("Тормозная жидкость DOT 4, 1 л", "brake-fluid-dot4", "AP-0017", FLUIDS, "Castrol", "650", 40, ALL),
    ("Амортизатор передний Sachs для Toyota", "shock-front-toyota", "AP-0018", SUSPENSION, "Sachs", "6800", 5, ["Camry", "Corolla"]),
    ("Амортизатор задний Sachs для Toyota", "shock-rear-toyota", "AP-0019", SUSPENSION, "Sachs", "4900", 4, ["Camry", "Corolla"]),
    ("Амортизатор передний Sachs для Kia и Hyundai", "shock-front-kia-hyundai", "AP-0020", SUSPENSION, "Sachs", "5200", 7, ["Rio", "Solaris"]),
    ("Пружина передней подвески Sachs для Polo", "spring-front-polo", "AP-0021", SUSPENSION, "Sachs", "3300", 3, ["Polo"]),
    ("Свеча зажигания NGK иридиевая", "spark-plug-iridium", "AP-0022", ELECTRICS, "NGK", "890", 60, TOYOTA + ["Rio", "Solaris"]),
    ("Свеча зажигания NGK стандартная", "spark-plug-standard", "AP-0023", ELECTRICS, "NGK", "420", 80, LADA + ["Polo"]),
    ("Лампа галогенная H7 Bosch", "bulb-h7", "AP-0024", ELECTRICS, "Bosch", "560", 45, ALL),
    ("Аккумулятор Bosch 60 А·ч", "battery-60ah", "AP-0025", ELECTRICS, "Bosch", "7900", 9, ALL),
    ("Щётки стеклоочистителя Bosch", "wipers-bosch", "AP-0026", ELECTRICS, "Bosch", "1500", 0, TOYOTA),
]


class Command(BaseCommand):
    help = "Заполняет каталог демонстрационными данными (можно запускать повторно)"

    def handle(self, *args, **options):
        categories = {}
        for name, slug in CATEGORIES:
            categories[name], _ = Category.objects.get_or_create(
                name=name, defaults={"slug": slug}
            )

        manufacturers = {}
        for name in MANUFACTURERS:
            manufacturers[name], _ = Manufacturer.objects.get_or_create(name=name)

        car_models = {}
        for (make_name, make_slug), models in CARS.items():
            make, _ = CarMake.objects.get_or_create(
                name=make_name, defaults={"slug": make_slug}
            )
            for model_name, year_from, year_to in models:
                car_models[model_name], _ = CarModel.objects.get_or_create(
                    make=make,
                    name=model_name,
                    year_from=year_from,
                    defaults={"year_to": year_to},
                )

        created = 0
        for name, slug, sku, category, manufacturer, price, stock, cars in PARTS:
            part, is_new = Part.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "sku": sku,
                    "category": categories[category],
                    "manufacturer": manufacturers[manufacturer],
                    "price": Decimal(price),
                    "stock": stock,
                    "description": "Учебная запчасть. Описание заполняется в admin panel.",
                },
            )
            if is_new:
                if cars is None:
                    part.compatible_models.set(car_models.values())
                else:
                    part.compatible_models.set(car_models[car] for car in cars)
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Готово. Новых запчастей: {created}"))