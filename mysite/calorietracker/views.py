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
from bootstrap_datepicker_plus import DateTimePickerInput, DatePickerInput

from chartjs.views.lines import BaseLineChartView

from .utilities import *
from datetime import date
import json
from django.core.serializers.json import DjangoJSONEncoder


class UpdateLogData(LoginRequiredMixin, UpdateView):
    """docstring for UpdateLogData."""

    # TODO: check if date does not overlap with existing log

    template_name = "calorietracker/update_logdata.html"
    model = Log
    fields = (
        "date",
        "weight",
        "calories_in",
        "calories_out",
        "activity_lvl",
    )

    success_url = reverse_lazy("analytics")

    def get_form(self):
        form = super().get_form()
        form.fields["date"].widget = DatePickerInput()
        return form


class Settings(LoginRequiredMixin, UpdateView):

    model = Setting
    fields = ["age", "sex", "height", "activity", "goal", "goal_weight", "goal_date"]
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
            .values("date", "weight", "calories_in", "calories_out")
        )

        df = pd.DataFrame(list(query_set))

        settings_set = Setting.objects.all().filter(user=self.request.user).values()

        df_settings = pd.DataFrame(list(settings_set))

        print(df)
        print(df_settings)

        # TODO: HANDLE UNITS CONVERSION FOR UI/FRONT END
        context["units_weight"] = "lbs"

        # Load the date range as n
        if self.request.method == "GET":
            rangeDrop_option = self.request.GET.get("rangeDrop", False)
            if rangeDrop_option in ["7", "14", "31"]:
                n = int(rangeDrop_option)
            else:
                n = len(df["weight"].tolist())
            context["n"] = n

        # Calculate TDEE, weight change, weight change rate
        if len(df["weight"].tolist()) < 14:
            # Not enough data to accurately calculate TDEE using weight changes vs calories in
            # So we use Harris-Benedict formula:
            # Men: BMR = 88.362 + (13.397 × weight in kg) + (4.799 × height in cm) - (5.677 × age in years)
            # Women: BMR = 447.593 + (9.247 × weight in kg) + (3.098 × height in cm) - (4.330 × age in years)
            if df_settings["sex"].all() == "M":
                context["BMR"] = round(
                    float(
                        88.362
                        + (13.397 * unit_conv(df["weight"].tolist()[-1], "lbs"))
                        + (4.799 * unit_conv(df_settings["height"], "in"))
                        - (5.677 * df_settings["age"])
                    ),
                )
            elif df_settings["sex"].all() == "F":
                context["BMR"] = round(
                    float(
                        447.593
                        + (9.247 * unit_conv(df["weight"].tolist()[-1], "lbs"))
                        + (3.098 * unit_conv(df_settings["height"], "in"))
                        - (4.330 * df_settings["age"])
                    ),
                )
            if df_settings["activity"].all() == "1":
                context["TDEE"] = context["BMR"] * 1.2
            elif df_settings["activity"].all() == "2":
                context["TDEE"] = context["BMR"] * 1.375
            elif df_settings["activity"].all() == "3":
                context["TDEE"] = context["BMR"] * 1.55
            elif df_settings["activity"].all() == "4":
                context["TDEE"] = context["BMR"] * 1.725
            elif df_settings["activity"].all() == "5":
                context["TDEE"] = context["BMR"] * 1.9

        else:
            # Enough data to accurately calculate TDEE using weight changes vs calories in
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

        # Populate time to goal and summary stats.
        context["goal_date"] = df_settings["goal_date"][0].date().strftime("%b-%d")
        context["time_left"] = (df_settings["goal_date"][0].date() - date.today()).days

        context["goal_weight"] = round(float(int(df_settings["goal_weight"])), 1)
        context["current_weight"] = moving_average(df["weight"].tolist())[-1]

        context["weight_to_go"] = context["goal_weight"] - context["current_weight"]
        context["weight_to_go_abs"] = abs(context["weight_to_go"])
        context["percent_to_goal"] = round(
            100
            * (
                1
                - abs(
                    context["weight_to_go"]
                    / (
                        moving_average(df["weight"].tolist())[0]
                        - context["goal_weight"]
                    )
                )
            )
        )

        context["target_deficit_per_week"] = round(
            (context["weight_to_go"] / context["time_left"]) * 7, 2
        )
        context["target_deficit_per_day"] = context["target_deficit_per_week"] / 7
        context["target_cal_deficit_per_day"] = context["target_deficit_per_day"] * 3500

        context["target_cal_in_per_day"] = round(
            abs(context["TDEE"] - context["target_cal_deficit_per_day"])
        )

        context["current_time_to_goal"] = abs(
            round(
                float(
                    (context["current_weight"] - context["goal_weight"])
                    / (context["daily_weight_change"])
                )
            )
        )

        # print(context)

        # Populate data_weight, data_cal_in and data_date for charts
        context["data_weight"] = df["weight"].tolist()[-n:]
        context["data_cal_in"] = df["calories_in"].tolist()[-n:]
        string_dates = [date.strftime("%b-%d") for date in df["date"].tolist()][-n:]
        context["data_date"] = json.dumps(string_dates)

        # Populate red, green, yellow for pie chart
        if df_settings["goal"].all() == "L" or df_settings["goal"].all() == "M":
            context["pie_labels"] = [
                "Days Above TDEE",
                "Days Below Target",
                "Days Above Target but Below TDEE",
            ]
            context["pie_cal_in_red"] = len(
                [
                    i
                    for i in df["calories_in"].tolist()[-n:]
                    if (i > abs(context["TDEE"]))
                ]
            )
            context["pie_cal_in_yellow"] = len(
                [
                    i
                    for i in df["calories_in"].tolist()[-n:]
                    if (context["target_cal_in_per_day"] < i < abs(context["TDEE"]))
                ]
            )
            context["pie_cal_in_green"] = len(
                [
                    i
                    for i in df["calories_in"].tolist()[-n:]
                    if i < context["target_cal_in_per_day"]
                ]
            )
        elif df_settings["goal"].all() == "G":
            context["pie_labels"] = [
                "Days Below TDEE",
                "Days Above Target",
                "Days Above TDEE but Below Target",
            ]
            context["pie_cal_in_red"] = len(
                [
                    i
                    for i in df["calories_in"].tolist()[-n:]
                    if (i < abs(context["TDEE"]))
                ]
            )
            context["pie_cal_in_yellow"] = len(
                [
                    i
                    for i in df["calories_in"].tolist()[-n:]
                    if (context["TDEE"] < i < abs(context["target_cal_in_per_day"]))
                ]
            )
            context["pie_cal_in_green"] = len(
                [
                    i
                    for i in df["calories_in"].tolist()[-n:]
                    if i > context["target_cal_in_per_day"]
                ]
            )

        # Populate json_data from query for table
        query_set = json.dumps(
            {"data": list(query_set)[-n:]},
            sort_keys=True,
            indent=1,
            cls=DjangoJSONEncoder,
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
