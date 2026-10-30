
from dataclasses import dataclass
from decimal import Decimal

from catalog.models import Part

CART_SESSION_KEY = "cart"


@dataclass
class CartLine:
    product: Part
    quantity: int

    @property
    def total(self):
        return self.product.price * self.quantity


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.items = self.session.get(CART_SESSION_KEY, {})

    def get_quantity(self, product):
        return self.items.get(str(product.pk), 0)

    def add(self, product, quantity=1, replace=False):
        key = str(product.pk)
        if not replace:
            quantity += self.get_quantity(product)

        quantity = min(quantity, product.stock)

        if quantity > 0:
            self.items[key] = quantity
        else:
            self.items.pop(key, None)

        self.save()
        return quantity

    def remove(self, product):
        self.items.pop(str(product.pk), None)
        self.save()

    def clear(self):
        self.items = {}
        self.save()

    def save(self):
        self.session[CART_SESSION_KEY] = self.items
        self.session.modified = True

    def lines(self):
        products = Part.objects.filter(
            pk__in=self.items.keys(),
            is_active=True
        )
        return [
            CartLine(product, self.items[str(product.pk)])
            for product in products
        ]

    def total_price(self):
        return sum(
            (line.total for line in self.lines()),
            Decimal("0")
        )

    def __len__(self):
        return sum(self.items.values())
