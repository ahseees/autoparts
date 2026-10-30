
from accounts.models import GarageCar

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from cart.cart import Cart
from catalog.models import Part

from .forms import OrderCreateForm
from .models import Order, OrderItem


def order_create(request):
    cart = Cart(request)
    lines = cart.lines()

    # Проверяем, что корзина не пустая
    if not lines:
        messages.warning(request, "Корзина пуста.")
        return redirect("cart:detail")

    # Проверка совместимости с автомобилями из гаража
    compatibility_warnings = []

    if request.user.is_authenticated:
        garage_model_ids = list(
            GarageCar.objects.filter(
                user=request.user
            ).values_list("car_model_id", flat=True)
        )

        if garage_model_ids:
            for line in lines:
                compatible = (
                    line.product.compatible_models.filter(
                        id__in=garage_model_ids
                    ).exists()
                )

                if not compatible:
                    compatibility_warnings.append(
                        line.product.name
                    )

    # Обработка оформления заказа
    if request.method == "POST":
        form = OrderCreateForm(request.POST)

        if form.is_valid():
            with transaction.atomic():

                # Блокируем товары на время оформления
                product_ids = sorted(
                    line.product.pk for line in lines
                )

                products = {
                    product.pk: product
                    for product in Part.objects.select_for_update()
                    .filter(
                        pk__in=product_ids,
                        is_active=True
                    )
                }

                # Проверяем актуальные остатки
                for line in lines:
                    product = products.get(
                        line.product.pk
                    )

                    if (
                        product is None
                        or product.stock < line.quantity
                    ):
                        messages.error(
                            request,
                            f"Недостаточно товара: {line.product.name}"
                        )
                        return redirect("cart:detail")

                # Создаём заказ
                order = form.save(commit=False)

                if request.user.is_authenticated:
                    order.user = request.user

                order.save()

                # Сохраняем позиции и списываем остатки
                for line in lines:
                    product = products[line.product.pk]

                    OrderItem.objects.create(
                        order=order,
                        part=product,
                        price=product.price,
                        quantity=line.quantity,
                    )

                    Part.objects.filter(
                        pk=product.pk
                    ).update(
                        stock=F("stock") - line.quantity
                    )

            # Очищаем корзину после успешного оформления
            cart.clear()

            return redirect(
                "orders:success",
                order_id=order.pk,
            )

    else:
        # Заполняем данные пользователя автоматически
        initial = {}

        if request.user.is_authenticated:
            user = request.user

            initial = {
                "full_name": user.get_full_name(),
                "email": user.email,
            }

        form = OrderCreateForm(
            initial=initial
        )

    # Отображаем страницу оформления
    return render(
        request,
        "orders/create.html",
        {
            "form": form,
            "lines": lines,
            "total": cart.total_price(),
            "compatibility_warnings": compatibility_warnings,
        },
    )


def order_success(request, order_id):
    return render(
        request,
        "orders/success.html",
        {"order_id": order_id},
    )


@login_required
@require_POST
def order_cancel(request, order_id):

    with transaction.atomic():

        order = get_object_or_404(
            Order.objects.select_for_update(),
            pk=order_id,
            user=request.user,
        )

        # Отменять можно только новые заказы
        if order.status != "new":
            messages.error(
                request,
                "Этот заказ уже нельзя отменить."
            )
            return redirect("profile")

        # Возвращаем товары на склад
        for item in order.items.select_related("part"):
            Part.objects.filter(
                pk=item.part_id
            ).update(
                stock=F("stock") + item.quantity
            )

        # Меняем статус заказа
        order.status = "cancelled"
        order.save(update_fields=["status"])

    messages.success(
        request,
        f"Заказ №{order.id} отменён. "
        "Товары возвращены на склад."
    )

    return redirect("profile")
