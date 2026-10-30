
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from accounts.models import Favorite, GarageCar
from .models import CarMake, CarModel, Category, Part


PARTS_PER_PAGE = 8

SORT_OPTIONS = {
    "name": ("name", "По названию"),
    "cheap": ("price", "Сначала дешёвые"),
    "expensive": ("-price", "Сначала дорогие"),
    "new": ("-created_at", "Сначала новые"),
}


def part_list(request, category_slug=None):
    category = None

    parts = Part.objects.filter(
        is_active=True
    ).select_related("category", "manufacturer")

    # Фильтрация по автомобилю из гаража
    garage_car_id = request.GET.get("garage_car")

    if garage_car_id:
        if request.user.is_authenticated:
            garage_car = GarageCar.objects.filter(
                id=garage_car_id,
                user=request.user
            ).first()

            if garage_car:
                parts = parts.filter(
                    compatible_models=garage_car.car_model
                ).distinct()
            else:
                parts = parts.none()
        else:
            parts = parts.none()

    # Фильтр по категории
    if category_slug:
        category = get_object_or_404(
            Category,
            slug=category_slug
        )
        parts = parts.filter(category=category)

    # Поиск по названию, артикулу и описанию
    query = request.GET.get("q", "").strip()

    if query:
        parts = parts.filter(
            search_index__contains=query.lower()
        )

    # Фильтр по марке автомобиля
    make = request.GET.get("make", "")
    model_names = []

    if make:
        model_names = list(
            CarModel.objects.filter(make__slug=make)
            .order_by("name")
            .values_list("name", flat=True)
            .distinct()
        )

    # Фильтр по модели
    model = request.GET.get("model", "")

    if model not in model_names:
        model = ""

    # Фильтр по году выпуска
    try:
        year = int(request.GET.get("year", ""))
    except ValueError:
        year = None

    car_filter = {}

    if make:
        car_filter["compatible_models__make__slug"] = make

    if model:
        car_filter["compatible_models__name"] = model

    if year:
        car_filter["compatible_models__year_from__lte"] = year
        car_filter["compatible_models__year_to__gte"] = year

    if car_filter:
        parts = parts.filter(**car_filter).distinct()

    # Сортировка
    sort = request.GET.get("sort", "name")

    if sort not in SORT_OPTIONS:
        sort = "name"

    parts = parts.order_by(SORT_OPTIONS[sort][0])

    # Постраничный вывод
    page = Paginator(
        parts,
        PARTS_PER_PAGE
    ).get_page(request.GET.get("page"))

    # ID товаров, добавленных в избранное
    favorite_part_ids = set()

    if request.user.is_authenticated:
        favorite_part_ids = set(
            Favorite.objects.filter(
                user=request.user
            ).values_list("part_id", flat=True)
        )

    context = {
        "category": category,
        "page": page,
        "query": query,
        "makes": CarMake.objects.all(),
        "make": make,
        "model_names": model_names,
        "model": model,
        "year": year,
        "sort": sort,
        "sort_options": SORT_OPTIONS,
        "garage_car_id": garage_car_id,
        "favorite_part_ids": favorite_part_ids,
    }

    return render(
        request,
        "catalog/part_list.html",
        context
    )


def part_detail(request, slug):
    part = get_object_or_404(
        Part.objects.select_related(
            "category",
            "manufacturer"
        ).prefetch_related(
            "compatible_models__make"
        ),
        slug=slug,
        is_active=True,
    )

    # Проверяем, находится ли товар в избранном
    is_favorite = False

    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(
            user=request.user,
            part=part
        ).exists()

    context = {
        "part": part,
        "is_favorite": is_favorite,
    }

    return render(
        request,
        "catalog/part_detail.html",
        context
    )
