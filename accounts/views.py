
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Part
from orders.models import Order

from .forms import GarageCarForm, ProfileEditForm, SignUpForm
from .models import Favorite, GarageCar, Notification


# ==========================================
# РЕГИСТРАЦИЯ
# ==========================================

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Вы зарегистрированы и вошли в магазин."
            )

            return redirect("catalog:part_list")
    else:
        form = SignUpForm()

    return render(
        request,
        "registration/signup.html",
        {"form": form}
    )


# ==========================================
# ЛИЧНЫЙ КАБИНЕТ
# ==========================================

@login_required
def profile(request):
    orders = (
        Order.objects
        .filter(user=request.user)
        .prefetch_related("items__part")
        .order_by("-created_at")
    )

    return render(
        request,
        "accounts/profile.html",
        {"orders": orders}
    )


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileEditForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Данные профиля успешно обновлены!"
            )

            return redirect("profile")
    else:
        form = ProfileEditForm(
            instance=request.user
        )

    return render(
        request,
        "accounts/profile_edit.html",
        {"form": form}
    )


# ==========================================
# ГАРАЖ ПОЛЬЗОВАТЕЛЯ
# ==========================================

@login_required
def garage(request):
    cars = (
        GarageCar.objects
        .filter(user=request.user)
        .select_related("car_model__make")
        .order_by("-created_at")
    )

    return render(
        request,
        "accounts/garage.html",
        {"cars": cars}
    )


@login_required
def garage_add(request):
    if request.method == "POST":
        form = GarageCarForm(request.POST)

        if form.is_valid():
            car = form.save(commit=False)
            car.user = request.user

            try:
                with transaction.atomic():
                    car.save()

            except IntegrityError:
                form.add_error(
                    None,
                    "Этот автомобиль уже добавлен в гараж."
                )

            else:
                messages.success(
                    request,
                    "Автомобиль успешно добавлен!"
                )

                return redirect("garage")
    else:
        form = GarageCarForm()

    return render(
        request,
        "accounts/garage_add.html",
        {"form": form}
    )


@login_required
@require_POST
def garage_delete(request, car_id):
    car = get_object_or_404(
        GarageCar,
        pk=car_id,
        user=request.user
    )

    car.delete()

    messages.success(
        request,
        "Автомобиль удалён из гаража."
    )

    return redirect("garage")


# ==========================================
# ИЗБРАННОЕ
# ==========================================

@login_required
def favorites(request):
    favorite_items = (
        Favorite.objects
        .filter(user=request.user)
        .select_related("part", "part__manufacturer")
        .order_by("-created_at")
    )

    return render(
        request,
        "accounts/favorites.html",
        {"favorite_items": favorite_items}
    )


@login_required
@require_POST
def favorite_toggle(request, part_id):
    part = get_object_or_404(
        Part,
        pk=part_id
    )

    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        part=part
    )

    if created:
        messages.success(
            request,
            "Запчасть добавлена в избранное."
        )
    else:
        favorite.delete()

        messages.success(
            request,
            "Запчасть удалена из избранного."
        )

    # Возвращаем пользователя туда,
    # откуда он нажал на сердечко.
    previous_page = request.META.get("HTTP_REFERER", "")

    if previous_page and url_has_allowed_host_and_scheme(
        url=previous_page,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(previous_page)

    # Если предыдущую страницу определить не удалось,
    # возвращаем пользователя в каталог.
    return redirect("catalog:part_list")


# ==========================================
# УВЕДОМЛЕНИЯ
# ==========================================

@login_required
def notifications(request):
    items = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "accounts/notifications.html",
        {"notifications": items}
    )


@login_required
@require_POST
def notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        user=request.user
    )

    notification.is_read = True
    notification.save(
        update_fields=["is_read"]
    )

    return redirect("notifications")
