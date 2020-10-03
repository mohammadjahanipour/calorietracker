from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
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
from datetime import date
import json


class Settings(LoginRequiredMixin, UpdateView):

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


class Analytics(LoginRequiredMixin, TemplateView):
    template_name = "calorietracker/analytics.html"

    def dispatch(self, request):

        if not Log.objects.filter(user=self.request.user).exists():
            messages.info(request, "You need to have made at least one log entry")
            return redirect(reverse_lazy("logdata"))

        return super().dispatch(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Load the user's logs as a DataFrame
        query_set = (
            Log.objects.all()
            .filter(user=self.request.user)
            .values("date", "weight", "calories_in", "calories_out", "steps",)
        )

        df = pd.DataFrame(list(query_set))

        # Load the date range as n
        if self.request.method == "GET":
            rangeDrop_option = self.request.GET.get("rangeDrop", False)
            if rangeDrop_option in ["7", "14", "31"]:
                n = int(rangeDrop_option)
            else:
                n = len(df["weight"].tolist())
            context["n"] = n

        # Calculate TDEE, weight change, weight change rate
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

        # Populate data_weight and data_date for chart
        context["data_weight"] = df["weight"].tolist()[-n:]
        string_dates = [date.strftime("%-m-%d-%y") for date in df["date"].tolist()][-n:]
        context["data_date"] = json.dumps(string_dates)

        # Populate json_data from query for table
        query_set = json.dumps(
            {"data": list(query_set)[-n:]}, sort_keys=True, indent=1, cls=str,
        )
        context["json_data"] = query_set

        return context


class LineChartJSONView(BaseLineChartView):
    pass


line_chart = TemplateView.as_view(template_name="line_chart.html")
line_chart_json = LineChartJSONView.as_view()


class LogData(LoginRequiredMixin, CreateView):
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
