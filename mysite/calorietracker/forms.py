
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model


class RegisterForm(UserCreationForm):

    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-user', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-user', 'placeholder': 'Repeat Password'}))

    class Meta:
        model = get_user_model()
        fields = ("username", "email", )

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control form-control-user', "placeholder": "Username"}),
            'email': forms.TextInput(attrs={'class': 'form-control form-control-user', "placeholder": "Email Address  *Optional"}),
        }


class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control form-control-user', 'placeholder': 'Username'}))

    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control form-control-user', 'placeholder': 'Password'}))
