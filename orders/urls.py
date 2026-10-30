
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("create/", views.order_create, name="create"),
    path(
        "success/<int:order_id>/",
        views.order_success,
        name="success",
    ),
    path("cancel/<int:order_id>/", views.order_cancel, name="cancel"),
]
