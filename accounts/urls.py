
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views


urlpatterns = [
    # Регистрация и авторизация
    path(
        "signup/",
        views.signup,
        name="signup",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path(
        "",
        include("django.contrib.auth.urls"),
    ),

    # Личный кабинет
    path(
        "profile/",
        views.profile,
        name="profile",
    ),
    path(
        "profile/edit/",
        views.profile_edit,
        name="profile_edit",
    ),

    # Гараж пользователя
    path(
        "garage/",
        views.garage,
        name="garage",
    ),
    path(
        "garage/add/",
        views.garage_add,
        name="garage_add",
    ),
    path(
        "garage/delete/<int:car_id>/",
        views.garage_delete,
        name="garage_delete",
    ),

    # Избранное
    path(
        "favorites/",
        views.favorites,
        name="favorites",
    ),
    path(
        "favorites/toggle/<int:part_id>/",
        views.favorite_toggle,
        name="favorite_toggle",
    ),

    # Уведомления
    path(
        "notifications/",
        views.notifications,
        name="notifications",
    ),
    path(
        "notifications/read/<int:notification_id>/",
        views.notification_read,
        name="notification_read",
    ),
]
