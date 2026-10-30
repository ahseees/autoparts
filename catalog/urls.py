from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.part_list, name="part_list"),
    path("category/<slug:category_slug>/", views.part_list, name="part_list_by_category"),
    path("part/<slug:slug>/", views.part_detail, name="part_detail"),
]