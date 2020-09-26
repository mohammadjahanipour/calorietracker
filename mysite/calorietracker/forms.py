from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Button
from .models import Log

from django.forms.widgets import DateInput


class RegisterForm(UserCreationForm):

    password1 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-user", "placeholder": "Password"}
        )
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-user",
                "placeholder": "Repeat Password",
            }
        )
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
        )

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control form-control-user",
                    "placeholder": "Username",
                }
            ),
            "email": forms.TextInput(
                attrs={
                    "class": "form-control form-control-user",
                    "placeholder": "Email Address  *Optional",
                }
            ),
        }


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control form-control-user", "placeholder": "Username"}
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control form-control-user", "placeholder": "Password"}
        )
    )


class DateInput(forms.DateInput):
    input_type = "date"


class LogForm(forms.ModelForm):
    class Meta:
        model = Log
        fields = (
            "date",
            "weight",
            "calories_in",
            "exercise_time",
            "exercise_type",
            "steps",
            "calories_out",
        )
        widgets = {
            "date": DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "POST"
        self.helper.layout = Layout(
            Row(
                Column(
                    Field("date", template="calorietracker/date.html"),
                    css_class="form-group col-md-2 mb-0",
                ),
                Column("weight", css_class="form-group col-md-2 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("calories_in", css_class="form-group col-md-2 mb-0"),
                Column("calories_out", css_class="form-group col-md-2 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("steps", css_class="form-group col-md-2 mb-0"),
                css_class="form-row",
            ),
            Row(
                Column("exercise_time", css_class="form-group col-md-2 mb-0"),
                Column("exercise_type", css_class="form-group col-md-4 mb-0"),
                css_class="form-row",
            ),
            Submit("submit", "Submit", css_class="btn-primary"),
        )
