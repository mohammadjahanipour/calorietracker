import json
from datetime import date, datetime, timedelta, timezone
import pandas as pd

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django_measurement.forms import MeasurementField

from ..base_models import Weight
from ..models import AnalyticsShareToken, Log, Setting
from ..utilities import (
    calculate_HarrisBenedict,
    calculate_TDEE,
    calculate_weight_change,
    interpolate,
    moving_average,
    rate,
    smooth_zero_weights_lerp,
    smooth_zero_weights_previous_avg,
)


class Analytics(TemplateView):
    template_name = "calorietracker/analytics.html"
    user = None  # Set in dispatch

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def dispatch(self, request, *args, **kwargs):
        # Set self.user
        if self.kwargs.get("uuid", False):
            # The analytics data of another user wants to be seen
            token = get_object_or_404(AnalyticsShareToken, uuid=self.kwargs.get("uuid"))
            self.user = token.user
            user = self.user
            info_string = (
                "You are viewing " + str(user.username) + "'s analytics dashboard"
            )
            messages.warning(request, info_string)

        else:
            # User wants to see their own analytics
            self.user = self.request.user
            user = self.user
            # no permission checks or activity checks are performed for now
            if user.is_authenticated is False:
                return redirect(reverse_lazy("login"))

        # Require at least 1 log
        if not Log.objects.filter(user=user).exists():
            messages.info(request, "You need to have made at least one log entry")
            return redirect(reverse_lazy("logdata"))

        # Check goal date is in the future
        x = list(Setting.objects.filter(user=user).values("goal_date"))[0]["goal_date"]
        if (x - datetime.now(timezone.utc)).days < 1:
            messages.info(
                request,
                "Please update your goal date as it is not far enough into the future",
            )
            return redirect(reverse_lazy("settings"))
        return super().dispatch(request)

    def warning_catches(self, goal_weight_change_per_week, weights):
        if abs(goal_weight_change_per_week.lb) > 2:
            messages.warning(
                self.request,
                "Warning: Your goal weight and/or date are very aggressive. We recommend setting goals that require between -2 to 2 lbs (-1 to 1 kgs) of weight change per week.",
            )
        if len(weights) < 10:
            messages.info(
                self.request,
                "Note: For accuracy, your targets & predictions will be formula based until you have more than 10 log entries",
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Querysets
        user = self.user
        self.logs = user.log_set.all().order_by("date")
        self.settings = user.setting
        context["username"] = user.username

        # Unit Initialization
        # Note that this uses the viewed user's preference, not necessarily the viewing user's
        if self.user.setting.unit_preference == "M":
            weights_label = "kgs"
            units_weight = "kg"
        else:
            weights_label = "lbs"
            units_weight = "lb"
        context["weights_label"] = weights_label

        # Smooth weights where weight == Weight(g=0) all calculations
        date_weight_tuples = self.logs.values_list("date", "weight").order_by("date")
        smoothed_date_weight_tuples = smooth_zero_weights_lerp(date_weight_tuples)
        smoothed_date_weight_tuples = smooth_zero_weights_previous_avg(
            date_weight_tuples
        )

        # Weight, Calories over Time Data: timestamps, weights, calories
        timestamps = [i[0] for i in smoothed_date_weight_tuples]
        all_weights = [i[1] for i in smoothed_date_weight_tuples]
        all_calories = list(
            self.logs.values_list("calories_in", flat=True).order_by("date")
        )

        # Handle dateRange Selector to trim data for rest of calculations
        if self.request.method == "GET":
            dateRange = self.request.GET.get("dateRange", False)
            if dateRange in ["14", "31", "90", "180"]:
                dateRange = int(dateRange)
                weights = all_weights[-dateRange:]
                calories = all_calories[-dateRange:]
                timestamps = timestamps[-dateRange:]
            else:
                dateRange = len(all_weights)
                weights = all_weights
                calories = all_calories

        context.update(
            {
                "dateRange": dateRange,
                "timestamps": json.dumps(
                    [date.strftime("%b. %d") for date in timestamps]
                ),
                "weights": [self.handle_weight_units(i, units_weight) for i in weights],
                "calories": calories,
            }
        )

        # Goals and Targets Card Data:
        context.update(self.get_data_goals_targets())

        # Header and Top Row Cards Data:
        context.update(
            self.get_data_top_row_cards(
                weights=weights,
                converted_weights=context["weights"],
                units=weights_label,
                calories=calories,
            )
        )

        # Daily Caloric Intake Target
        context.update(
            self.get_daily_caloric_intake_target(tdee=context["estimated_tdee"])
        )

        # Caloric Intake Breakdown Chart Data:
        context.update(
            self.get_pie_chart_data(
                TDEE=context["estimated_tdee"],
                dailycaltarget=context["daily_caloric_intake_target"],
                calories=calories,
                goal=self.settings.goal,
            )
        )

        # Weekly Summary tables Data:
        data_weekly_table = self.get_data_weekly_table(
            all_weights=[
                self.handle_weight_units(i, units_weight) for i in all_weights
            ],
            TDEE=context["estimated_tdee"],
            calories=all_calories,
            units=weights_label,
        )
        context["weeklyjson_data"] = json.dumps(
            {"data": data_weekly_table},
            sort_keys=True,
            indent=1,
            cls=DjangoJSONEncoder,
        )
        # Goal for weekly summary tables conditional coloring
        context["goal"] = self.settings.goal

        # Display warnings as needed
        self.warning_catches(context["goal_weight_change_per_week"], weights)

        # Convert Weight types to floats using units_weight for displaying
        context = {
            k: self.handle_weight_units(v, units_weight) for k, v in context.items()
        }

        # Handle misc. formatting
        if context["projected_time_to_goal_days"] < 0:
            context["projected_time_to_goal_days"] = "TBD"
            context["projected_time_to_goal_date"] = "TBD"
        else:
            context["projected_time_to_goal_days"] = int(
                context["projected_time_to_goal_days"]
            )

        context["weight_change"] = "{:+}".format(context["weight_change"])
        context["weight_to_go"] = "{:+}".format(context["weight_to_go"])
        context["current_rate_of_weight_change"] = "{:+}".format(
            context["current_rate_of_weight_change"]
        )

        # Debug print context keys and vals
        # print("\n".join("{!r}: {!r},".format(k, v) for k, v in context.items()))

        return context

    def get_data_goals_targets(self):
        """
        Computes:
           current_weight, goal_weight, goal_date, weight_to_go, goal_weight_change_per_week, percent_to_goal
        Returns:
            dict
        """
        current_weight = self.get_current_weight(self.logs)
        initial_weight = self.logs[0].weight
        if (self.settings.goal_weight - initial_weight) != 0:
            percent_to_goal = round(
                100
                * (
                    1
                    - (
                        (self.settings.goal_weight - current_weight)
                        / (self.settings.goal_weight - initial_weight)
                    )
                )
            )
        else:
            percent_to_goal = 100

        goals_and_targets = {
            "current_weight": current_weight,
            "goal_weight": self.settings.goal_weight,
            "weight_to_go": self.settings.goal_weight - current_weight,
            "percent_to_goal": percent_to_goal,
            "goal_date": self.settings.goal_date.strftime("%b. %-d"),
            "time_left": self.settings.time_to_goal,
            "goal_weight_change_per_week": (
                self.settings.goal_weight - self.get_current_weight(self.logs)
            )
            / (self.settings.time_to_goal / 7),
        }

        return goals_and_targets

    def get_data_top_row_cards(self, weights, converted_weights, units, calories):
        """
        Computes:
            weight_change, estimated_tdee, projected_time_to_goal (days), current_rate_of_weight_change
        Returns:
            dict
        """
        if len(weights) < 10:
            weight_change = calculate_weight_change(weights, len(weights), False)
            return {
                "weight_change": weight_change,
                "estimated_tdee": calculate_HarrisBenedict(
                    weight=weights[-1],
                    sex=self.settings.sex,
                    height=self.settings.height,
                    age=self.settings.age,
                    activity=self.settings.activity,
                ),
                "current_rate_of_weight_change": (weight_change / len(weights)) * 7,
                "projected_time_to_goal_days": -1,
                "projected_time_to_goal_date": -1,
            }
        weight_change = calculate_weight_change(weights, len(weights), True)

        estimated_tdee = calculate_TDEE(
            CI=calories,
            weights=converted_weights,
            n=len(weights),
            units=units,
            smooth=True,
        )

        current_rate_of_weight_change = (weight_change / len(weights)) * 7  # per week

        if weight_change != Weight(lb=0.0):
            projected_time_to_goal_days = (
                self.settings.goal_weight - self.get_current_weight(self.logs)
            ) / (weight_change / len(weights))
            projected_time_to_goal_date = date.today() + timedelta(
                days=projected_time_to_goal_days
            )
        else:
            projected_time_to_goal_days = -1
            projected_time_to_goal_date = -1

        return {
            "weight_change": weight_change,
            "estimated_tdee": estimated_tdee,
            "current_rate_of_weight_change": current_rate_of_weight_change,
            "projected_time_to_goal_days": projected_time_to_goal_days,
            "projected_time_to_goal_date": projected_time_to_goal_date,
        }

    def get_daily_caloric_intake_target(self, tdee):
        """
        Computes:
            daily_caloric_intake_target
        Returns:
            dict
        """

        goal_daily_caloric_deficit = (
            (self.settings.goal_weight - self.get_current_weight(self.logs))
            / (self.settings.time_to_goal)
        ).lb * 3500
        print(goal_daily_caloric_deficit)
        # change = CI + CO
        # CI = change - CO

        daily_caloric_intake_target = round(goal_daily_caloric_deficit - tdee)

        return {
            "daily_caloric_intake_target": daily_caloric_intake_target,
        }

    def get_data_weekly_table(
        self,
        all_weights,
        calories,
        TDEE,
        units,
    ):

        date_format = "%Y-%W"
        df = pd.DataFrame(
            list(
                (
                    Log.objects.all()
                    .filter(user=self.user)
                    .values("id", "date", "weight", "calories_in")
                    .order_by("date")
                )
            )
        )
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["weight"] = all_weights

        weeklycalories_in_mean = (
            df.groupby(df.date.dt.strftime(date_format)).calories_in.mean().tolist()
        )
        weeklycalories_in_total = (
            df.groupby(df.date.dt.strftime(date_format)).calories_in.sum().tolist()
        )
        weeklyweights = df.groupby(df.date.dt.strftime(date_format)).weight.median().tolist()
        weeklydates = df.groupby(df.date.dt.strftime(date_format)).date.agg(["first", "last"])
        weeklydatestarts = weeklydates["first"].tolist()
        weeklydateends = weeklydates["last"].tolist()

        weeklytabledata = []
        for i in range(len(weeklyweights)):
            entry = {}
            entry["week_number"] = i
            entry["weeks"] = (
                weeklydatestarts[i].strftime("%b. %-d")
                + " - "
                + weeklydateends[i].strftime("%b. %-d")
            )
            entry["weeklycalories_in_mean"] = round(weeklycalories_in_mean[i])
            entry["weeklycalories_in_total"] = round(weeklycalories_in_total[i])
            entry["weeklyweights"] = round(weeklyweights[i], 2)

            # First week
            if i == 0:
                entry["weeklyweightchange"] = 0.00
                entry["TDEE"] = "N/A"
            else:
                entry["weeklyweightchange"] = "{:+}".format(
                    round(weeklyweights[i] - weeklyweights[i - 1], 2)
                )
                # Calculate TDEE for the week using smoothing with a window of 3
                entry["TDEE"] = calculate_TDEE(
                    calories[(i - 1) * 7: (i + 1) * 7],
                    all_weights[(i - 1) * 7: (i + 1) * 7],
                    n=len(all_weights),
                    units=units,
                    smooth=True,
                    window=3,
                )

            # Current Week
            if i == len(weeklyweights) - 1:
                entry["TDEE"] = "TBD"
            weeklytabledata.append(entry)

        return weeklytabledata

    @staticmethod
    def get_pie_chart_data(TDEE, dailycaltarget, calories, goal):
        # pie_labels, pie_red, pie_yellow, pie_green
        # returns a dict
        TDEE = abs(TDEE)
        dailycaltarget = abs(dailycaltarget)
        calories_in = calories
        if goal == "L" or goal == "M":
            pie_labels = [
                "Days Above TDEE",
                "Days Below Target",
                "Days Above Target but Below TDEE",
            ]
            pie_red = len([i for i in calories_in if (i > TDEE)])
            pie_green = len([i for i in calories_in if i < dailycaltarget])
            pie_yellow = len([i for i in calories_in if (dailycaltarget < i < TDEE)])

        elif goal == "G":
            pie_labels = [
                "Days Below TDEE",
                "Days Above Target",
                "Days Above TDEE but Below Target",
            ]
            pie_red = len([i for i in calories_in if (i < TDEE)])
            pie_green = len([i for i in calories_in if i > dailycaltarget])
            pie_yellow = len([i for i in calories_in if (TDEE < i < dailycaltarget)])

        return {
            "pie_labels": pie_labels,
            "pie_red": pie_red,
            "pie_yellow": pie_yellow,
            "pie_green": pie_green,
        }

    @staticmethod
    def handle_weight_units(x, units):
        # if x is measurement object return x.units rounded to 1 decimal place
        # else returns x
        if not type(x) == Weight:
            return x
        else:
            return round(getattr(x, units), 1)

    @staticmethod
    def get_current_weight(logs):
        if not len(logs):
            current_weight = Weight(g=0)
        elif len(logs) < 5:
            # Not enough logs to give a smooth avg current weight
            # Return most recent weight
            current_weight = logs[len(logs) - 1].weight
        else:
            # Return a moving average of non-zero last n weights
            all_weights = [
                log_weight["weight"] for log_weight in list(logs.values("weight"))
            ]
            all_nonzero_weights = [w for w in all_weights if not w == Weight(g=0.0)]
            if len(all_nonzero_weights):
                current_weight = moving_average(all_nonzero_weights)[-1]
            else:
                current_weight = logs[len(logs) - 1].weight
        return current_weight
