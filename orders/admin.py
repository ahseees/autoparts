
from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("part", "price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "email")
    readonly_fields = ("created_at",)
    inlines = [OrderItemInline]
