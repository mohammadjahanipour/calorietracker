from django.db import transaction
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, FormView, UpdateView
from django.urls import reverse_lazy
from .forms import RegisterForm, LoginForm, LogForm
from .models import Log

from django.contrib.auth.views import LoginView, LogoutView

from django.contrib.auth.mixins import LoginRequiredMixin


class HomePage(TemplateView):
    template_name = "calorietracker/home.html"


class Profile(TemplateView):
    template_name = "calorietracker/profile.html"


class Charts(TemplateView):
    template_name = "calorietracker/charts.html"


class Analytics(TemplateView):
    template_name = "calorietracker/analytics.html"


class LogData(CreateView):
    model = Log
    form_class = LogForm
    template_name = "calorietracker/logdata.html"


class Register(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy("login")
    template_name = "calorietracker/register.html"


class Login(LoginView):
    form_class = LoginForm
    template_name = "calorietracker/login.html"


class Logout(LogoutView):
    """Logout"""
