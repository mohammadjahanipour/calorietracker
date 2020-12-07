import csv
from io import TextIOWrapper
import dateutil.parser
import pandas as pd

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, RedirectView, UpdateView
from measurement.measures import Distance, Mass, Weight

from ..forms import ImportCSVForm
from ..models import Log


def merge_csv_weights(user, overwrite, weights_dict):
    """
    Paramaters
    user:
        django user class
    overwrite: Overwrite logged weights if True
        bool
    weights_dict:
        ordered dict of date: Weight
    """

    for date, weight in weights_dict.items():
        # print(date, weight)
        # print("Resolving date", date, "weight:", weight)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(weight=weight)
                # print("Overwrite is True! Updated Weight")
        else:
            # print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=weight, calories_in=0
            )  # Note we have calories_in as null=False so we place 0 and assume the user can import calories separately

    return True


def merge_csv_calories_in(user, overwrite, calories_in_dict):
    """
    Paramaters
    user:
        django user class
    overwrite: Overwrite logged weights if True
        bool
    calories_in_dict
        dict of {date: objects of class day}
    """

    for date, calories_in in calories_in_dict.items():
        # print(date, calories_in)
        # print("Resolving date", date, "calories_in:", calories_in)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(
                    calories_in=calories_in
                )
                # print("Overwrite is True! Updated calories_in")
        else:
            # print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=Weight(lb=0.0), calories_in=calories_in
            )  # Note we have weight as null=False so we place 0 and assume the user can import weights separately

    return True


class ImportCSV(FormView):
    template_name = "calorietracker/importCSVdata.html"
    form_class = ImportCSVForm
    success_url = reverse_lazy("logs")

    def dispatch(self, request):
        if not self.request.user.is_authenticated:
            return redirect(reverse_lazy("login"))
        return super().dispatch(request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integration_name"] = "CSV"

        return context

    def validate_csv(self, form):
        # Probably worth doing this check first anyway
        validation_error_messages = []
        data_file = self.request.FILES["data_file"]
        if not data_file.name.endswith(".csv"):
            validation_error_messages.append(
                "Invalid file extension - only csv files are accepted"
            )

        MAX_UPLOAD_SIZE = 104857600  # 100MB
        if data_file.size > MAX_UPLOAD_SIZE:
            validation_error_messages.append(
                "File size too large. Max upload size is 100MB"
            )

        with TextIOWrapper(
            self.request.FILES["data_file"].file, encoding=self.request.encoding
        ) as f:
            reader = csv.reader(f)
            available_headers = next(reader, None)
            try:
                Date_index = available_headers.index("Date")
            except:
                validation_error_messages.append(
                    "Missing header (case sensitive): Date"
                )
            try:
                Weight_index = available_headers.index("Weight")
            except:
                validation_error_messages.append(
                    "Missing header (case sensitive): Weight"
                )
            try:
                CaloriesIn_index = available_headers.index("Calories_In")
            except:
                validation_error_messages.append(
                    "Missing header (case sensitive): Calories_In"
                )

            weights_dict = {}
            calories_in_dict = {}
            row_number = 0
            # Only continue if all headers are present
            if not validation_error_messages:
                for row in reader:
                    row_number += 1
                    try:
                        # Skip rows with empty cells
                        if row[Date_index] in (None, ""):
                            continue
                        if row[Weight_index] in (None, ""):
                            continue
                        if row[CaloriesIn_index] in (None, ""):
                            continue
                    except:
                        continue
                    try:
                        # Parse out the date format
                        if form.cleaned_data["date_format"] == "MDY":
                            fmtd_date = dateutil.parser.parse(row[Date_index])
                        elif form.cleaned_data["date_format"] == "DMY":
                            fmtd_date = dateutil.parser.parse(
                                row[Date_index], dayfirst=True
                            )
                        elif form.cleaned_data["date_format"] == "YMD":
                            fmtd_date = dateutil.parser.parse(
                                row[Date_index], yearfirst=True
                            )
                        elif form.cleaned_data["date_format"] == "YDM":
                            fmtd_date = dateutil.parser.parse(
                                row[Date_index], yearfirst=True, dayfirst=True
                            )
                    except ValueError:
                        validation_error_messages.append(
                            "Could not parse date: "
                            + str(row[Date_index] + " at row number " + str(row_number))
                        )

                    try:
                        # Parse the weight
                        if form.cleaned_data["weight_units"] == "lb":
                            weights_dict[fmtd_date] = Weight(lb=row[Weight_index])
                        elif form.cleaned_data["weight_units"] == "kg":
                            weights_dict[fmtd_date] = Weight(kg=row[Weight_index])
                    except ValueError:
                        validation_error_messages.append(
                            "Could not parse weight: "
                            + str(
                                row[Weight_index] + " at row number " + str(row_number)
                            )
                        )
                    try:
                        # Parse the calories in
                        calories_in_dict[fmtd_date] = int(float(row[CaloriesIn_index]))
                    except:
                        validation_error_messages.append(
                            "Could not parse calories_in: "
                            + str(
                                row[CaloriesIn_index]
                                + " at row number "
                                + str(row_number)
                            )
                        )

        if validation_error_messages:
            validation_error_messages = [
                "Failed to validate CSV file:"
            ] + validation_error_messages

            if settings.DEBUG:
                raise ValidationError(" ".join(validation_error_messages))
            else:
                for i in validation_error_messages:
                    messages.info(
                        self.request,
                        i,
                    )
                return False

        else:
            messages.info(
                self.request,
                "Importing! For large imports, this may take some time. Thank you for your patience!",
            )
            merge_csv_weights(
                user=self.request.user,
                overwrite=form.cleaned_data["csv_overwrite"],
                weights_dict=weights_dict,
            )

            merge_csv_calories_in(
                user=self.request.user,
                overwrite=form.cleaned_data["csv_overwrite"],
                calories_in_dict=calories_in_dict,
            )

            return True

    def form_valid(self, form):
        if self.request.method == "POST":
            if not self.validate_csv(form):
                return super().form_invalid(form)

            # Re-Actualize input streak
            self.request.user.streak.actualize_input_streak()

            return super().form_valid(form)
