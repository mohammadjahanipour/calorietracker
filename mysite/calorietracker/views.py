from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView, FormView, UpdateView
from django.urls import reverse_lazy
from .forms import RegisterForm, LoginForm, LogForm
from .models import Log, Setting
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from bootstrap_datepicker_plus import DateTimePickerInput

from chartjs.views.lines import BaseLineChartView
from .utilities import *


class Settings(UpdateView):

    model = Setting
    fields = ["age", "height", "activity", "goal", "goal_date"]
    template_name = "calorietracker/settings.html"
    success_url = reverse_lazy("settings")

    def get_object(self):
        return self.request.user.setting

    def get_form(self):
        form = super().get_form()
        form.fields["goal_date"].widget = DateTimePickerInput()
        return form


class HomePage(TemplateView):
    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    template_name = "calorietracker/home.html"


class Profile(TemplateView):
    template_name = "calorietracker/profile.html"


class Analytics(TemplateView):
    template_name = "calorietracker/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user_authenticated = self.request.user
        n = 102
        context["n"] = n
        print(
            "Summary Analytics for user",
            current_user_authenticated.username,
            "over last",
            n,
            "days",
        )

        df = pd.DataFrame(
            list(
                Log.objects.all()
                .filter(user=current_user_authenticated)
                .values(
                    "id",
                    "created_at",
                    "updated_at",
                    "deleted",
                    "date",
                    "weight",
                    "calories_in",
                    "calories_out",
                    "steps",
                )
            )
        )

        context["TDEE"] = round(
            calculate_TDEE(
                df["calories_in"].tolist(),
                df["weight"].tolist(),
                n=n,
                smooth=True,
                window=3,
            )
        )
        context["weight_change_raw"], context["weight_change_smooth"] = (
            round(weight_change(df["weight"].tolist(), n=n, smooth=False), 1),
            round(weight_change(df["weight"].tolist(), n=n, smooth=True), 1),
        )
        context["daily_weight_change"] = round(context["weight_change_smooth"] / n, 2)
        context["weekly_weight_change"] = round(context["daily_weight_change"] * 7, 2)

        return context


class LineChartJSONView(BaseLineChartView):
    def get_labels(self):
        """Return 7 labels for the x-axis."""
        return ["January", "February", "March", "April", "May", "June", "July"]

    def get_providers(self):
        """Return names of datasets."""
        return ["Central", "Eastside", "Westside"]

    def get_data(self):
        """Return 3 datasets to plot."""

        return [
            [75, 44, 92, 11, 44, 95, 35],
            [41, 92, 18, 3, 73, 87, 92],
            [87, 21, 94, 3, 90, 13, 65],
        ]


line_chart = TemplateView.as_view(template_name="line_chart.html")
line_chart_json = LineChartJSONView.as_view()


class LogData(CreateView):
    model = Log
    form_class = LogForm
    template_name = "calorietracker/logdata.html"
    success_url = reverse_lazy("analytics")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class Register(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy("login")
    template_name = "calorietracker/register.html"


class Login(LoginView):
    form_class = LoginForm
    template_name = "calorietracker/login.html"


class Logout(LogoutView):
    """Logout"""


class PasswordChange(PasswordChangeView):
    """PasswordChange"""

    success_url = reverse_lazy("home")
    template_name = "calorietracker/change-password.html"
