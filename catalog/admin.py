from django.contrib import admin

from .models import CarMake, CarModel, Category, Manufacturer, Part


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(CarMake)
class CarMakeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ("make", "name", "year_from", "year_to")
    list_filter = ("make",)
    search_fields = ("name", "make__name")
    list_select_related = ("make",)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "manufacturer", "price", "stock", "is_active")
    list_editable = ("price", "stock", "is_active")
    list_filter = ("is_active", "category", "manufacturer")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("category", "manufacturer")
    filter_horizontal = ("compatible_models",)