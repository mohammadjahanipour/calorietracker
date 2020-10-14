from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, CreateView, FormView, UpdateView
from django.urls import reverse_lazy
from .forms import (
    RegisterForm,
    LoginForm,
    LogDataForm,
    MeasurementWidget,
    SettingForm,
    ImportMFPForm,
)
from .models import Log, Setting, Feedback
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from bootstrap_datepicker_plus import DateTimePickerInput, DatePickerInput

from chartjs.views.lines import BaseLineChartView

from .utilities import *
from .mfpintegration import *
from datetime import date, timedelta, datetime, timezone
import json
from django.core.serializers.json import DjangoJSONEncoder

from django_measurement.forms import MeasurementField
from measurement.measures import Distance, Weight
from django.core.exceptions import ValidationError

from .models import MFPCredentials
from django import forms


from django.views.generic.base import RedirectView
from django.core.exceptions import ObjectDoesNotExist


class ImportMFPCredentials(RedirectView):

    """
    Redirects either to create or updateview
    """

    # OPTIMIZE: users can go to both update and create mfp views
    # they should be redirected in those views also or that case should be handled

    permanent = False
    query_string = False
    pattern_name = "import-credentials-mfp-create"

    def get_redirect_url(self, *args, **kwargs):

        try:
            self.request.user.mfpcredentials
            self.pattern_name = "import-credentials-mfp-update"

        except ObjectDoesNotExist:
            pass

        return super().get_redirect_url(*args, **kwargs)


class ImportMFPCredentialsCreate(LoginRequiredMixin, CreateView):
    """docstring for MFPCredentials."""

    # Todo: Catch login errors: myfitnesspal.exceptions.MyfitnesspalLoginError

    model = MFPCredentials
    fields = (
        "username",
        "password",
    )

    success_url = reverse_lazy("importmfp")

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            client = myfitnesspal.Client(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                unit_aware=True,
            )

        except myfitnesspal.exceptions.MyfitnesspalLoginError:
            messages.info(
                self.request,
                "Error connecting to MyFitnessPal with the provided information. Please check your MyFitnessPal account settings and try again.",
            )
            return super().form_invalid(form)

        messages.success(self.request, "MyFitnessPal Credentials Saved")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["password"].widget = forms.PasswordInput()
        return form


class ImportMFPCredentialsUpdate(LoginRequiredMixin, UpdateView):
    """docstring for MFPCredentials."""

    # Todo: Catch login errors: myfitnesspal.exceptions.MyfitnesspalLoginError

    model = MFPCredentials
    fields = (
        "username",
        "password",
    )

    success_url = reverse_lazy("importmfp")

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        try:
            client = myfitnesspal.Client(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                unit_aware=True,
            )

        except myfitnesspal.exceptions.MyfitnesspalLoginError:
            messages.info(
                self.request,
                "Error connecting to MyFitnessPal with the provided information. Please check your MyFitnessPal account settings and try again.",
            )
            return super().form_invalid(form)

        messages.success(self.request, "MyFitnessPal Credentials Updated")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["password"].widget = forms.PasswordInput()
        return form

    def get_object(self):
        return self.request.user.mfpcredentials


class ImportMFP(FormView):
    template_name = "calorietracker/importdata.html"
    form_class = ImportMFPForm
    success_url = reverse_lazy("logs")

    def dispatch(self, request):

        if not self.request.user.is_authenticated:
            return redirect(reverse_lazy("login"))
        if not MFPCredentials.objects.filter(user=self.request.user).exists():
            messages.info(request, "Please enter your MyFitnessPal credentials")
            return redirect(reverse_lazy("import-credentials-mfp"))

        return super().dispatch(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integration_name"] = "MyFitnessPal"

        return context

    def form_valid(self, form):
        if self.request.method == "POST":
            # todo: potentially this needs a lot of api response handling back to the user
            # todo: create a loading animation/page on form submission so that user does not spam click submit

            try:
                client = myfitnesspal.Client(
                    username=self.request.user.mfpcredentials.username,
                    password=self.request.user.mfpcredentials.password,
                    unit_aware=True,
                )
            except myfitnesspal.exceptions.MyfitnesspalLoginError:
                messages.info(
                    self.request,
                    "Error connecting to MyFitnessPal with the provided information. Please check your MyFitnessPal account settings and try again.",
                )
                return redirect(reverse_lazy("import-credentials-mfp"))

            if form.cleaned_data["mfp_data_select"] == "Weights":
                weights_dict = get_weights_by_range(
                    client,
                    form.cleaned_data["mfp_start_date"],
                    form.cleaned_data["mfp_end_date"],
                )
                merge_mfp_weights(
                    user=self.request.user,
                    overwrite=form.cleaned_data["mfp_overwrite"],
                    weights_dict=weights_dict,
                )
            elif form.cleaned_data["mfp_data_select"] == "CI":
                days_dict = get_days_by_range(
                    client,
                    form.cleaned_data["mfp_start_date"],
                    form.cleaned_data["mfp_end_date"],
                )
                merge_mfp_calories_in(
                    user=self.request.user,
                    overwrite=form.cleaned_data["mfp_overwrite"],
                    days_dict=days_dict,
                )

        return super().form_valid(form)


class Feedback(LoginRequiredMixin, CreateView):
    """docstring for Feedback."""

    model = Feedback
    fields = (
        "comment",
        "contact_email",
    )

    success_url = reverse_lazy("feedback")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Feedback Submited")
        return super().form_valid(form)


class UpdateLogData(LoginRequiredMixin, UpdateView):
    """docstring for UpdateLogData."""

    # TODO: check if date does not overlap with existing log
    model = Log
    form_class = LogDataForm
    template_name = "calorietracker/update_logdata.html"

    success_url = reverse_lazy("analytics")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def get_queryset(self):
        return Log.objects.filter(user=self.request.user)

    def get_form(self):
        form = super().get_form()
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class LogData(LoginRequiredMixin, CreateView):

    # TODO: check if date does not overlap with existing log

    model = Log
    form_class = LogDataForm
    template_name = "calorietracker/logdata.html"

    success_url = reverse_lazy("analytics")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def get_form(self):
        form = super().get_form()
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user

        query_set = Log.objects.filter(user=self.request.user).filter(
            date=form.cleaned_data.get("date")
        )
        if query_set:
            pk = str(
                (
                    Log.objects.filter(user=self.request.user)
                    .filter(date=form.cleaned_data.get("date"))
                    .values_list("id", flat=True)
                )[0]
            )
            messages.warning(
                self.request,
                mark_safe(
                    "A log for "
                    + str(form.cleaned_data.get("date"))
                    + " already exists. You can update <a href='/logdata/"
                    + pk
                    + "/update'>this entry here</a>"
                ),
            )
            return super().form_invalid(form)
        return super().form_valid(form)


class Settings(LoginRequiredMixin, UpdateView):

    # TODO: do rounding on outputed height

    model = Setting
    form_class = SettingForm

    template_name = "calorietracker/settings.html"

    success_url = reverse_lazy("settings")

    def get_object(self):
        return self.request.user.setting

    def get_form(self):
        form = super().get_form()
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


class ViewLogs(TemplateView):
    template_name = "calorietracker/logstable.html"

    def load_data(self, **kwargs):
        self.query_set = (
            Log.objects.all()
            .filter(user=self.request.user)
            .values("id", "date", "weight", "calories_in")
            .order_by("date")
        )
        df_query = pd.DataFrame(list(self.query_set))
        settings_set = Setting.objects.all().filter(user=self.request.user).values()
        df_settings = pd.DataFrame(list(settings_set))

        self.units = df_settings["unit_preference"].all()

        # weights, calories_in, dates
        self.rawweights = df_query["weight"].tolist()
        self.weights = df_query["weight"].tolist()
        self.weights = [round(x.lb, 2) for x in self.weights]
        self.calories_in = df_query["calories_in"].tolist()
        self.dates = df_query["date"].tolist()
        self.ids = df_query["id"].tolist()

        # Unit control
        # NOTE: all initial calculations above are done in imperial.
        # We convert to metric as needed at the very end here.
        if self.units == "I":
            self.unitsweight = "lbs"
        elif self.units == "M":
            self.unitsweight = "kgs"
            self.weights = [round(x.kg, 2) for x in self.rawweights]

        self.logtabledata = self.get_logtabledata()

    def dispatch(self, request):

        if not self.request.user.is_authenticated:
            return redirect(reverse_lazy("login"))
        if not Log.objects.filter(user=self.request.user).exists():
            messages.info(request, "You need to have made at least one log entry")
            return redirect(reverse_lazy("logdata"))

        return super().dispatch(request)

    def get_logtabledata(self):
        logtabledata = []
        for i in range(len(self.weights)):
            entry = {}
            entry["id"] = self.ids[i]
            entry["date"] = self.dates[i]
            entry["weight"] = self.weights[i]
            entry["calories_in"] = self.calories_in[i]
            logtabledata.append(entry)
        return logtabledata

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.load_data()

        context = {
            "units": self.units,
            "units_weight": self.unitsweight,
            "logjson_data": json.dumps(
                {"data": self.logtabledata},
                sort_keys=True,
                indent=1,
                cls=DjangoJSONEncoder,
            ),
        }
        return context


class Analytics(LoginRequiredMixin, TemplateView):
    template_name = "calorietracker/analytics.html"

    def load_data(self, **kwargs):
        self.query_set = (
            Log.objects.all()
            .filter(user=self.request.user)
            .values("id", "date", "weight", "calories_in")
            .order_by("date")
        )
        df_query = pd.DataFrame(list(self.query_set))
        settings_set = Setting.objects.all().filter(user=self.request.user).values()
        df_settings = pd.DataFrame(list(settings_set))

        # age, height, sex, activity, goaldate, goalweight
        self.age = df_settings["age"]
        self.height = df_settings["height"].all().cm
        self.sex = df_settings["sex"].all()
        self.activity = df_settings["activity"].all()
        self.goaldate = df_settings["goal_date"][0].date()
        self.goalweight = round(float(df_settings["goal_weight"].all().lb), 1)
        self.goal = df_settings["goal"].all()
        self.units = df_settings["unit_preference"].all()

        # weights, calories_in, dates
        self.rawweights = df_query["weight"].tolist()
        self.weights = df_query["weight"].tolist()
        # replace any weight entries that are not smoothed with smoothed weight
        if Weight(lb=0) in self.weights:
            messages.info(
                self.request,
                "Found some log entries where weight is 0; We use smoothing to extrapolate your correct weight for these logs.",
            )
            self.smoothed_weights = self.smooth_zero_weights(method="lerp")
            self.smoothed_weights = self.smooth_zero_weights(method="previous_avg")

        # we do all calculations in weight = pounds, calories in = caloires. We convert to unit preference later.
        self.weights = [round(x.lb, 2) for x in self.smoothed_weights]
        self.calories_in = df_query["calories_in"].tolist()
        self.dates = df_query["date"].tolist()
        self.ids = df_query["id"].tolist()

        # Load the date range as self.n
        if self.request.method == "GET":
            rangeDrop_option = self.request.GET.get("rangeDrop", False)
            if rangeDrop_option in ["7", "14", "31"]:
                self.n = int(rangeDrop_option)
            else:
                self.n = len(self.weights)

        if len(self.weights) < 5:
            self.currentweight = self.weights[-1]
        else:
            self.currentweight = moving_average(self.weights)[-1]

        # Calculate TDEE
        if len(self.weights) < 10:
            # Not enough data to accurately calculate TDEE using weight changes vs calories in, so we use Harris-Benedict formula
            self.TDEE = self.HarrisBenedict()
        else:
            # Enough data to accurately calculate TDEE using weight changes vs calories in
            self.TDEE = calculate_TDEE(
                self.calories_in,
                self.weights,
                n=self.n,
                smooth=True,
                window=3,
            )

        # Weight change
        self.weightchangeraw = weight_change(self.weights, n=self.n, smooth=False)
        self.weightchangesmooth = weight_change(self.weights, n=self.n, smooth=True)

        # Weight change rate
        self.dailyweightchange = round(self.weightchangesmooth / self.n, 2)
        if len(self.weights) > 7:
            self.weeklyweightchange = round(self.dailyweightchange * 7, 2)
        else:
            self.weeklyweightchange = 0.00

        # Progress timeleft, weight to go
        self.timeleft = (self.goaldate - date.today()).days
        self.weighttogo = round(self.goalweight - self.currentweight, 1)
        self.weighttogoabs = abs(self.weighttogo)

        # Targets
        if self.timeleft == 0:
            self.timeleft = 1
        self.targetweeklydeficit = round((self.weighttogo / self.timeleft) * 7, 2)
        self.targetdailycaldeficit = self.targetweeklydeficit * 3500 / 7
        self.dailycaltarget = round(abs(self.TDEE) + self.targetdailycaldeficit)

        # Time to goal
        if len(self.weights) > 1:
            self.currenttimetogoal = abs(
                round((self.weighttogo) / (self.dailyweightchange), 0)
            )
            if self.currenttimetogoal != float("inf"):
                self.currentgoaldate = (
                    date.today() + timedelta(days=self.currenttimetogoal)
                ).strftime("%b. %-d")
            else:
                self.currentgoaldate = "TBD"
        else:
            self.currentgoaldate = "TBD"
            self.currenttimetogoal = "TBD"

        if (self.weights[0] - self.goalweight) != 0:
            self.percenttogoal = round(
                100 * (1 - abs(self.weighttogo / (self.weights[0] - self.goalweight))),
                1,
            )
        else:
            self.percenttogoal = 0
        if self.percenttogoal < 0:
            self.percenttogoal = 0

        # Unit control
        # NOTE: all initial calculations above are done in imperial.
        # We convert to metric as needed at the very end here.
        if self.units == "I":
            self.unitsweight = "lbs"
        elif self.units == "M":
            self.unitsweight = "kgs"
            self.weights = [round(x.kg, 2) for x in self.rawweights]
            self.currentweight = unit_conv(self.currentweight, "lbs")
            self.weightchangesmooth = unit_conv(self.weightchangesmooth, "lbs")
            self.weightchangeraw = unit_conv(self.weightchangeraw, "lbs")
            self.weeklyweightchange = unit_conv(self.weeklyweightchange, "lbs")
            self.weighttogo = unit_conv(self.weighttogo, "lbs")
            self.weighttogoabs = unit_conv(self.weighttogoabs, "lbs")
            self.goalweight = unit_conv(self.goalweight, "lbs")
            self.targetweeklydeficit = unit_conv(self.targetweeklydeficit, "lbs")

        self.weeklytabledata = self.get_weeklytabledata()

    def dispatch(self, request):

        if not self.request.user.is_authenticated:
            return redirect(reverse_lazy("login"))
        if not Log.objects.filter(user=self.request.user).exists():
            messages.info(request, "You need to have made at least one log entry")
            return redirect(reverse_lazy("logdata"))

        settings_vars = [
            "age",
            "sex",
            "height",
            "activity",
            "goal",
            "goal_weight",
            "goal_date",
            "unit_preference",
        ]
        for var in settings_vars:
            if not (
                list(Setting.objects.filter(user=self.request.user).values(var))[0][var]
            ):
                messages.info(request, "Please fill out your settings. Missing: " + var)
                return redirect(reverse_lazy("settings"))

        # Check goal date is in the future
        x = list(Setting.objects.filter(user=self.request.user).values("goal_date"))[0][
            "goal_date"
        ]
        if (x - datetime.now(timezone.utc)).days < 0:
            messages.info(
                request,
                "Please update your goal date as it is not far enough into the future",
            )
            return redirect(reverse_lazy("settings"))
        return super().dispatch(request)

    def smooth_zero_weights(self, method="lerp"):
        smoothed_weights = []

        if method == "lerp":
            # first get all weight, dates as list of tuplesall_weights = list(
            all_logs = (
                Log.objects.filter(user=self.request.user)
                .values_list("date", "weight")
                .order_by("date")
            )  # list of tuples (date, weight)
            dates, weights = [e[0] for e in all_logs], [e[1] for e in all_logs]
            nonzeroweight_indices = [
                i for i, e in enumerate(weights) if e != Weight(g=0)
            ]

            for i in range(len(dates)):
                if weights[i] == Weight(g=0):
                    # print("index", i, "has weight 0")
                    # find previous date and weight that is non zero
                    previous_found = next_found = False
                    prev_search_index = next_search_index = i
                    while prev_search_index >= 0 and previous_found == False:
                        if prev_search_index in nonzeroweight_indices:
                            w1 = weights[prev_search_index]
                            y1 = dates[prev_search_index]
                            previous_found = True
                        else:
                            prev_search_index -= 1

                    # find next date and weight that is non zero
                    while next_search_index < len(weights) and next_found == False:
                        if next_search_index in nonzeroweight_indices:
                            w2 = weights[next_search_index]
                            y2 = dates[next_search_index]
                            next_found = True
                        else:
                            next_search_index += 1

                    if not (next_found and previous_found):
                        # print("ERROR, failed to find a valid bounding weight entry")
                        # print("next_found", next_found)
                        # print("previous_found", previous_found)
                        smoothed_weights.append(weights[i])
                        continue
                    else:
                        interpolated_weight = interpolate(w1, w2, y1, y2, dates[i])
                        # print(w1.lb, w2.lb, y1, y2, dates[i])
                        # print("interpolated as", interpolated_weight.lb)
                        # update this entry with interpolated_weight
                        smoothed_weights.append(interpolated_weight)
                        # print(
                        #     "Updated",
                        #     dates[i].strftime("%m/%d/%Y"),
                        #     "with weight",
                        #     interpolated_weight,
                        # )
                else:
                    smoothed_weights.append(weights[i])
            return smoothed_weights

        if method == "previous_avg":
            all_weights = list(
                Log.objects.filter(user=self.request.user)
                .values_list("date", "weight")
                .order_by("date")
            )  # list of tuples (date, weight)

            for i in range(len(all_weights)):
                entry = all_weights[i]  # (date, weight)
                if entry[1] == Weight(g=0.0):
                    # get last 10 weights
                    previous = all_weights[i - 11 : i - 1]
                    # print("previous 10 weights", previous)

                    # remove entries where weight is 0
                    previous = [
                        value[1] for value in previous if value[1] != Mass(g=0.0)
                    ]

                    # calculate average. if there is no elements in previous, set average to 0
                    if len((previous)):
                        average = sum([value.lb for value in previous]) / len(previous)
                    else:
                        average = Weight(g=0.0)

                    # update this entry with average
                    smoothed_weights.append(Weight(lb=average))
                    # print(
                    #     "Updated",
                    #     entry[0].strftime("%m/%d/%Y"),
                    #     "with weight",
                    #     Weight(lb=average),
                    # )
                else:
                    smoothed_weights.append(entry[1])
            return smoothed_weights

    def HarrisBenedict(self, **kwargs):
        # Estimate TDEE in the absence of enouhg data
        weight = unit_conv(self.currentweight, "lbs")

        if self.sex == "M":
            BMR = round(
                -1
                * float(
                    88.362
                    + (13.397 * weight)
                    + (4.799 * self.height)
                    - (5.677 * self.age)
                ),
            )
        elif self.sex == "F":
            BMR = round(
                -1
                * float(
                    447.593
                    + (9.247 * weight)
                    + (3.098 * self.height)
                    - (4.330 * self.age)
                ),
            )
        if self.activity == "1":
            TDEE = BMR * 1.2
        elif self.activity == "2":
            TDEE = BMR * 1.375
        elif self.activity == "3":
            TDEE = BMR * 1.55
        elif self.activity == "4":
            TDEE = BMR * 1.725
        elif self.activity == "5":
            TDEE = BMR * 1.9

        return round(TDEE)

    def get_pie_chart_data(self):
        TDEE = abs(self.TDEE)
        dailycaltarget = abs(self.dailycaltarget)
        calories_in = self.calories_in[-self.n :]
        if self.goal == "L" or self.goal == "M":
            pie_labels = [
                "Days Above TDEE",
                "Days Below Target",
                "Days Above Target but Below TDEE",
            ]
            pie_red = len([i for i in calories_in if (i > TDEE)])
            pie_green = len([i for i in calories_in if i < dailycaltarget])
            pie_yellow = len([i for i in calories_in if (dailycaltarget < i < TDEE)])

        elif self.goal == "G":
            pie_labels = [
                "Days Below TDEE",
                "Days Above Target",
                "Days Above TDEE but Below Target",
            ]
            pie_red = len([i for i in calories_in if (i < TDEE)])
            pie_green = len([i for i in calories_in if i > dailycaltarget])
            pie_yellow = len([i for i in calories_in if (TDEE < i < dailycaltarget)])

        return pie_labels, pie_red, pie_yellow, pie_green

    def warning_catches(self):
        if abs(self.targetweeklydeficit) > 2:
            messages.warning(
                self.request,
                "Warning: Your goal weight and/or date are very aggressive. We recommend setting goals that require between -2 to 2 lbs (-1 to 1 kgs) of weight change per week.",
            )
        if len(self.weights) < 10:
            messages.info(
                self.request,
                "Note: For accuracy, your targets & predictions will be formula based until you have more than 10 log entries",
            )

    def get_weeklytabledata(self):
        df = pd.DataFrame(list(self.query_set))
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["weight"] = self.smoothed_weights
        if self.units == "I":
            df["weight"] = df["weight"].apply(lambda x: round(x.lb, 2))
        else:
            df["weight"] = df["weight"].apply(lambda x: round(x.kg, 2))

        weeklycalories_in_mean = (
            df.groupby(df.date.dt.strftime("%W")).calories_in.mean().tolist()
        )
        weeklycalories_in_total = (
            df.groupby(df.date.dt.strftime("%W")).calories_in.sum().tolist()
        )
        weeklyweights = df.groupby(df.date.dt.strftime("%W")).weight.mean().tolist()
        weeklydates = df.groupby(df.date.dt.strftime("%W")).date.agg(["first", "last"])
        weeklydatestarts = weeklydates["first"].tolist()
        weeklydateends = weeklydates["last"].tolist()

        weeklytabledata = []
        for i in range(len(weeklyweights)):
            entry = {}
            entry["week_number"] = i
            entry["weeks"] = (
                weeklydatestarts[i].strftime("%b-%-d")
                + " - "
                + weeklydateends[i].strftime("%b-%-d")
            )
            entry["weeklycalories_in_mean"] = round(weeklycalories_in_mean[i])
            entry["weeklycalories_in_total"] = round(weeklycalories_in_total[i])
            entry["weeklyweights"] = round(weeklyweights[i], 2)
            if i == 0:
                entry["weeklyweightchange"] = 0.00
                entry["TDEE"] = "N/A"
            else:
                entry["weeklyweightchange"] = round(
                    weeklyweights[i] - weeklyweights[i - 1], 2
                )
                entry["TDEE"] = calculate_TDEE(
                    self.calories_in[(i - 1) * 7 : (i + 1) * 7],
                    self.weights[(i - 1) * 7 : (i + 1) * 7],
                    n=len(self.weights),
                    units=self.unitsweight,
                    smooth=True,
                    window=3,
                )
            if i == len(weeklyweights) - 1:
                entry["TDEE"] = self.TDEE
            weeklytabledata.append(entry)

        return weeklytabledata

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.load_data()
        self.warning_catches()

        context = {
            "units": self.units,
            "units_weight": self.unitsweight,
            "n": self.n,
            # "chartVar": self.chartVar,
            "TDEE": self.TDEE,
            "weight_change_raw": self.weightchangeraw,
            "weight_change_smooth": self.weightchangesmooth,
            "daily_weight_change": self.dailyweightchange,
            "weekly_weight_change": self.weeklyweightchange,
            "goal_date": self.goaldate.strftime("%b-%-d"),
            "time_left": self.timeleft,
            "goal": self.goal,
            "goal_weight": self.goalweight,
            "current_weight": round(self.currentweight, 1),
            "weight_to_go": self.weighttogo,
            "weight_to_go_abs": self.weighttogoabs,
            "target_weekly_deficit": self.targetweeklydeficit,
            "target_daily_cal_deficit": self.targetdailycaldeficit,
            "daily_cal_target": self.dailycaltarget,
            "current_time_to_goal": self.currenttimetogoal,
            "current_goal_date": self.currentgoaldate,
            "percent_to_goal": self.percenttogoal,
            "data_weight": self.weights[-self.n :],
            "data_cal_in": self.calories_in[-self.n :],
            "data_date": json.dumps(
                [date.strftime("%b-%d") for date in self.dates][-self.n :]
            ),
            "weeklyjson_data": json.dumps(
                {"data": self.weeklytabledata},
                sort_keys=True,
                indent=1,
                cls=DjangoJSONEncoder,
            ),
        }

        # Populate red, green, yellow for pie chart
        (
            context["pie_labels"],
            context["pie_red"],
            context["pie_yellow"],
            context["pie_green"],
        ) = self.get_pie_chart_data()

        return context


class LineChartJSONView(BaseLineChartView):
    pass


line_chart = TemplateView.as_view(template_name="line_chart.html")
line_chart_json = LineChartJSONView.as_view()


class Register(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy("login")
    template_name = "calorietracker/register.html"

    def form_valid(self, form):
        # flash message assumes that the registration view redirects directly to a relavent page or that the flash message wont be retrieved in the login view
        messages.info(
            self.request,
            "Predictions will be inaccurate until you update your settings",
        )
        return super().form_valid(form)


class Login(LoginView):
    form_class = LoginForm
    template_name = "calorietracker/login.html"


class Logout(LogoutView):
    """Logout"""


class PasswordChange(PasswordChangeView):
    """PasswordChange"""

    success_url = reverse_lazy("home")
    template_name = "calorietracker/change-password.html"


class Purchase(LoginRequiredMixin):
    """docstring for Purchase."""
