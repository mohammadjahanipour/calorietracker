import json
from datetime import date, datetime, timedelta, timezone
import pandas as pd

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django_measurement.forms import MeasurementField
from measurement.measures import Distance, Mass, Weight

from .models import Log, Setting
from .utilities import calculate_TDEE, moving_average, unit_conv, weight_change


def rate(x1, x2, y1, y2):
    # x1, x2 are measruement objects for which we calculate the change
    # y1, y2 are date objects for which we calculate the time delta in days
    weight_change = x2 - x1
    time_delta = int((y2 - y1).days)
    # print("weight_change", weight_change.lb)
    # print("time_delta", time_delta, "days")
    return weight_change / time_delta


def interpolate(x1, x2, y1, y2, y):

    slope = rate(x1, x2, y1, y2)
    days_since_x1 = int((y - y1).days)
    output = x1 + (slope * days_since_x1)

    return output


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
        self.weights = self.smoothed_weights = df_query["weight"].tolist()
        # replace any weight entries that are not smoothed with smoothed weight
        if Weight(lb=0) in self.weights:
            messages.info(
                self.request,
                "Found some log entries weight is 0. We use smoothing to extrapolate your correct weight for these logs.",
            )
            self.smoothed_weights = self.smooth_zero_weights(method="lerp")
            self.smoothed_weights = self.smooth_zero_weights(method="previous_avg")

        # we do all calculations in weight = pounds, calories in = caloires. We convert to unit preference later.
        self.weights = [round(x.lb, 2) for x in self.smoothed_weights]
        self.calories_in = df_query["calories_in"].tolist()
        if 0 in self.calories_in:
            messages.info(
                self.request,
                "Found log entries where caloric intake is 0. We recommend updating these entries for to maintain accuracy.",
            )
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
            if self.n < 10:
                n = 10
            else:
                n = self.n
            self.TDEE = calculate_TDEE(
                self.calories_in,
                self.weights,
                n=n,
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
            self.weights = [round(x.kg, 2) for x in self.smoothed_weights]
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
            # first get all weight, dates as list of tuples
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
                        smoothed_weights.append(weights[i])
                        continue
                    else:
                        interpolated_weight = interpolate(w1, w2, y1, y2, dates[i])
                        smoothed_weights.append(interpolated_weight)
                else:
                    smoothed_weights.append(weights[i])
            return smoothed_weights

        if method == "previous_avg":
            all_weights = list(
                Log.objects.filter(user=self.request.user)
                .values_list("date", "weight")
                .order_by("date")
            )  # list of tuples (date, weight)

            n = 11
            for i in range(len(all_weights)):
                entry = all_weights[i]  # (date, weight)
                if entry[1] == Weight(g=0.0):
                    # get last n weights
                    previous = all_weights[i - n : i - 1]
                    previous = [
                        value[1] for value in previous if value[1] != Mass(g=0.0)
                    ]
                    # calculate average.
                    if len((previous)):
                        average = sum([value.lb for value in previous]) / len(previous)
                    else:
                        # if there is no elements in previous, set average to last 10 elements of nonzeroweights
                        nonzeroweights = [
                            value[1].lb
                            for value in all_weights
                            if value[1] != Mass(g=0.0)
                        ]
                        if len(nonzeroweights[-10:-1]) != 0:
                            average = sum(nonzeroweights[-10:-1]) / len(
                                nonzeroweights[-10:-1]
                            )
                        else:
                            average = 0
                    smoothed_weights.append(Weight(lb=average))
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
