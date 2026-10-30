
from django import forms


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(
        label="Количество",
        min_value=1,
        max_value=99,
        initial=1
    )
    replace = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput
    )
