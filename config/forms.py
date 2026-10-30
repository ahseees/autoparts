
from django import forms


class BootstrapFormMixin:
    """Добавляет оформление Bootstrap ко всем полям формы."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            elif not isinstance(
                field.widget,
                (forms.CheckboxInput, forms.HiddenInput)
            ):
                field.widget.attrs["class"] = "form-control"
