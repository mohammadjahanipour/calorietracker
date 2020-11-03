from collections import OrderedDict
from datetime import date, timedelta, datetime, timezone
from threading import Thread
import myfitnesspal

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, RedirectView, UpdateView
from measurement.measures import Distance, Mass, Weight
from bootstrap_datepicker_plus import DatePickerInput


from ..forms import ImportMFPForm
from ..models import Log, MFPCredentials


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


@start_new_thread
def auto_sync_helper(user, start_date, client):
    connection.close()
    start_date = start_date.replace(tzinfo=timezone.utc).date()
    end_date = datetime.today().replace(tzinfo=timezone.utc).date()

    weights_dict = get_weights_by_range(
        client=client, start_date=start_date, end_date=end_date
    )
    merge_mfp_weights(
        user=user,
        overwrite=False,
        weights_dict=weights_dict,
    )

    days_dict = get_days_by_range(
        client=client, start_date=start_date, end_date=end_date
    )
    merge_mfp_calories_in(
        user=user,
        overwrite=False,
        days_dict=days_dict,
    )

    # todo implement updating model MFPCredentials attribute last_mfp_log_date_synced to most recent mfp date with weight or calories


def get_days_by_range(client, start_date, end_date):
    """
    Parameters:
        client
            myfitnesspal.Client
        start_date
            datetime.date
        end_day
            datetime.date
    Returns dict of {date: objects of class day}
        day: https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py

    """

    delta = timedelta(days=1)
    output = {}
    while start_date <= end_date:
        data = client.get_date(start_date)
        output[start_date] = data
        start_date += delta

    return output


def get_weights_by_range(client, start_date, end_date):
    """
    Parameters:
        client
            myfitnesspal.Client
        start_date
            datetime.date
        end_day
            datetime.date
    Returns OrderedDict of weights
        {date: measurement}

    """
    weights_raw = client.get_measurements("Weight", start_date, end_date)
    if client.user_metadata["unit_preferences"]["weight"] == "pounds":
        weights = {k: Weight(lb=v) for k, v in weights_raw.items()}
    else:
        weights = {k: Weight(kg=v) for k, v in weights_raw.items()}

    return weights


def get_weight_by_date(client, date):
    """
    returns
    day
        https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py
    """

    weight = get_weights_by_range(client, date, date)
    return weight


def get_day_by_date(client, date):
    """
    returns
    day
        https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py
    """

    day = client.get_date(date)
    return day


def merge_mfp_weights(user, overwrite, weights_dict):
    """
    Paramaters
    user:
        django user class
    overwrite: Overwrite logged weights if True
        bool
    weights_dict:
        ordered dict of date: weight
    """

    for date, weight in weights_dict.items():
        # print(date, weight)
        # print("Resolving date", date, "weight:", weight)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(weight=weight)
                # print("Overwrite is True! Updated Weight")
            elif Log.objects.filter(user=user).filter(date=date).values_list("weight")[
                0
            ][0] == Weight(lb=0):
                Log.objects.filter(user=user).filter(date=date).update(weight=weight)
                # print("Weight is 0 for date! Updated Weight")
        else:
            # print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=weight, calories_in=0
            )  # Note we have calories_in as null=False so we place 0 and assume the user can import calories separately

    return True


def merge_mfp_calories_in(user, overwrite, days_dict):
    """
    Paramaters
    user:
        django user class
    overwrite: Overwrite logged weights if True
        bool
    days_dict
        dict of {date: objects of class day}
    """

    for date, day in days_dict.items():
        try:
            calories_in = day.totals["calories"].C
        except:
            continue
        # print(date, calories_in)
        # print("Resolving date", date, "calories_in:", calories_in)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(
                    calories_in=calories_in
                )
                # print("Overwrite is True! Updated calories_in")
            elif (
                Log.objects.filter(user=user)
                .filter(date=date)
                .values_list("calories_in")[0][0]
                == 0
            ):
                Log.objects.filter(user=user).filter(date=date).update(
                    calories_in=calories_in
                )
                # print("Calories for date is 0! Updated calories_in")

        else:
            # print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=Weight(lb=0.0), calories_in=calories_in
            )  # Note we have weight as null=False so we place 0 and assume the user can import weights separately

    return True


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
    fields = ("username", "password", "mfp_autosync", "mfp_autosync_startdate")

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

        messages.success(self.request, "MyFitnessPal Settings Saved")

        # if auto-sync is checked, we should do a full import of the user's logs
        mfp_autosync = form.cleaned_data["mfp_autosync"]
        if mfp_autosync:
            # run full sync here
            auto_sync_helper(
                user=self.request.user,
                start_date=form.cleaned_data["mfp_autosync_startdate"],
                client=client,
            )
            messages.info(
                self.request,
                "MFP Auto-sync: Importing! For large imports, this may take some time. Thank you for your patience!",
            )
            return redirect(reverse_lazy("logs"))

        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["password"].widget = forms.PasswordInput()
        form.fields["mfp_autosync"].label = "MFP Auto-sync"
        form.fields[
            "mfp_autosync"
        ].help_text = "Checking this box will automatically import ALL your caloric intake and weight data from MFP. This will pull in new data as you enter it in MFP and will not overwrite any logs entered on CalorieTracker.io."
        form.fields["mfp_autosync_startdate"].label = "MFP Auto-sync Start Date"
        form.fields[
            "mfp_autosync_startdate"
        ].help_text = "The starting date from which to automatically import MFP logs to CalorieTracker.io"
        form.fields["mfp_autosync_startdate"].widget = DatePickerInput(
            format="%m/%d/%Y"
        )
        return form


class ImportMFPCredentialsUpdate(LoginRequiredMixin, UpdateView):
    """docstring for MFPCredentials."""

    model = MFPCredentials
    fields = ("username", "password", "mfp_autosync", "mfp_autosync_startdate")
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

        messages.success(self.request, "MyFitnessPal Settings Updated")
        # if auto-sync is checked, we should do a full import of the user's logs
        mfp_autosync = form.cleaned_data["mfp_autosync"]
        if mfp_autosync:
            # run full sync here
            auto_sync_helper(
                user=self.request.user,
                start_date=form.cleaned_data["mfp_autosync_startdate"],
                client=client,
            )
            messages.info(
                self.request,
                "MFP Auto-sync: Importing! For large imports, this may take some time. Thank you for your patience!",
            )
            return redirect(reverse_lazy("logs"))

        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["password"].widget = forms.PasswordInput()
        form.fields["mfp_autosync"].label = "MFP Auto-sync"
        form.fields[
            "mfp_autosync"
        ].help_text = "Checking this box will automatically import ALL your caloric intake and weight data from MFP. This will pull in new data as you enter it in MFP and will not overwrite any logs entered on CalorieTracker.io."
        form.fields["mfp_autosync_startdate"].label = "MFP Auto-sync Start Date"
        form.fields[
            "mfp_autosync_startdate"
        ].help_text = "The starting date from which to automatically import MFP logs to CalorieTracker.io"
        form.fields["mfp_autosync_startdate"].widget = DatePickerInput(
            format="%m/%d/%Y"
        )
        return form

    def get_object(self):
        return self.request.user.mfpcredentials


class ImportMFP(FormView):
    template_name = "calorietracker/importMFPdata.html"
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
