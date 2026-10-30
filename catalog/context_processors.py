from .models import Category


def categories(request):
    """Список категорий для меню на каждой странице."""
    return {"nav_categories": Category.objects.all()}