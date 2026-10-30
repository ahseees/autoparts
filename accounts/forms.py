
from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from config.forms import BootstrapFormMixin
from .models import User


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label="Электронная почта")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Электронная почта",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
        }

from django import forms

from .models import GarageCar


class GarageCarForm(forms.ModelForm):
    class Meta:
        model = GarageCar
        fields = ["car_model", "year"]

        labels = {
            "car_model": "Марка и модель автомобиля",
            "year": "Год выпуска",
        }

        widgets = {
            "car_model": forms.Select(
                attrs={"class": "form-select"}
            ),
            "year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Например, 2018",
                    "min": "1900",
                    "max": "2100",
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        car_model = cleaned_data.get("car_model")
        year = cleaned_data.get("year")

        if car_model and year is not None:
            if not (
                car_model.year_from
                <= year
                <= car_model.year_to
            ):
                self.add_error(
                    "year",
                    (
                        f"Для модели {car_model.name} "
                        f"допустимы годы выпуска "
                        f"с {car_model.year_from} "
                        f"по {car_model.year_to}."
                    )
                )

        return cleaned_data
