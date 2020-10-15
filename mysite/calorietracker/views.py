from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.utils.safestring import mark_safe
from django.shortcuts import redirect, render, get_object_or_404
from django import forms
from django.views.generic import (
    TemplateView,
    CreateView,
    FormView,
    UpdateView,
    RedirectView,
)
from .forms import (
    RegisterForm,
    LoginForm,
    LogDataForm,
    MeasurementWidget,
    SettingForm,
    ImportMFPForm,
)
from .models import Log, Setting, Feedback, MFPCredentials
from django.core.exceptions import ValidationError, ObjectDoesNotExist

from chartjs.views.lines import BaseLineChartView

from .mfpintegration import *
import json, pandas as pd

from threading import Thread

from .analytics_view import Analytics


def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return decorator


@start_new_thread
def merge_helper(user, form, client):
    connection.close()
    if form.cleaned_data["mfp_data_select"] == "Weights":
        weights_dict = get_weights_by_range(
            client,
            form.cleaned_data["mfp_start_date"],
            form.cleaned_data["mfp_end_date"],
        )
        merge_mfp_weights(
            user=user,
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
            user=user,
            overwrite=form.cleaned_data["mfp_overwrite"],
            days_dict=days_dict,
        )


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
            merge_helper(user=self.request.user, form=form, client=client)
            messages.info(
                self.request,
                "Importing! For large imports, this may take some time. Thank you for your patience!",
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
