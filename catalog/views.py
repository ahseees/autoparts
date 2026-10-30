from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import CarMake, CarModel, Category, Part

PARTS_PER_PAGE = 8

# значение параметра ?sort= : (поле для order_by, подпись в списке)
SORT_OPTIONS = {
    "name": ("name", "По названию"),
    "cheap": ("price", "Сначала дешёвые"),
    "expensive": ("-price", "Сначала дорогие"),
    "new": ("-created_at", "Сначала новые"),
}


def part_list(request, category_slug=None):
    category = None
    parts = Part.objects.filter(is_active=True).select_related("category", "manufacturer")
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        parts = parts.filter(category=category)

    # Поиск без учёта регистра (в том числе для кириллицы)
    query = request.GET.get("q", "").strip()
    if query:
        parts = parts.filter(search_index__contains=query.lower())

    # Фильтр по автомобилю: марка -> модель -> год
    make = request.GET.get("make", "")
    model_names = []
    if make:
        model_names = list(
            CarModel.objects.filter(make__slug=make)
            .order_by("name")
            .values_list("name", flat=True)
            .distinct()
        )
    model = request.GET.get("model", "")
    if model not in model_names:
        model = ""
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

    # Сортировка только из белого списка
    sort = request.GET.get("sort", "name")
    if sort not in SORT_OPTIONS:
        sort = "name"
    parts = parts.order_by(SORT_OPTIONS[sort][0])

    page = Paginator(parts, PARTS_PER_PAGE).get_page(request.GET.get("page"))

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
    }
    return render(request, "catalog/part_list.html", context)


def part_detail(request, slug):
    part = get_object_or_404(
        Part.objects.select_related("category", "manufacturer").prefetch_related(
            "compatible_models__make"
        ),
        slug=slug,
        is_active=True,
    )
    return render(request, "catalog/part_detail.html", {"part": part})