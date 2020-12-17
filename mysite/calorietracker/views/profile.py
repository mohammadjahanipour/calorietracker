import json
from datetime import datetime, timedelta, timezone

from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin


from ..base_models import Weight
from ..models import Log, Setting, Streak
from ..utilities import (
    moving_average,
    rate,
    interpolate,
    smooth_zero_weights_lerp,
    smooth_zero_weights_previous_avg,
)
from friendship.models import Friend, FriendshipRequest


class Profile(LoginRequiredMixin, TemplateView):
    template_name = "calorietracker/profile.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user from slug if present
        if not self.kwargs.get("slug"):
            user = self.request.user
        else:
            user = User.objects.get(username=self.kwargs.get("slug"))

        # Querysets
        logs = user.log_set.all().order_by("date")
        settings = user.setting
        # Actualize input streak before querying streaks
        user.streak.actualize_input_streak()
        streaks = user.streak

        # Context Data
        # Header and Top row cards
        context.update(
            {
                "username": user.username,
                "userID": user.id,
                "join_date": user.date_joined.date,
                "last_seen_date": user.last_login.date,
                "log_count": len(logs),
                "current_streak": streaks.input_streak,
                "log_rate": self.get_log_rate(logs),
            }
        )

        current_weight = self.get_current_weight(logs)
        goal_weight = settings.goal_weight
        weight_to_go = goal_weight - current_weight
        raw_measures = [current_weight, goal_weight, weight_to_go]  # of type Weight

        # Unit Handling
        if settings.unit_preference == "M":
            weights_label = "kgs"
            units_weight = "kg"
        else:
            weights_label = "lbs"
            units_weight = "lb"

        # Convert each value of type Weight to Weight.lb or Weight.kg
        current_weight, goal_weight, weight_to_go = [
            self.handle_weight_units(i, units_weight) for i in raw_measures
        ]

        # Goals Card data
        context.update(
            {
                "weights_label": weights_label,
                "current_weight": current_weight,
                "weight_to_go": "{:+}".format(weight_to_go),
                "goal_weight": goal_weight,
                "goal_date": settings.goal_date.strftime("%b. %-d"),
                "time_left": settings.time_to_goal,
            }
        )

        # Smooth weights where weight == Weight(g=0) for charts
        date_weight_tuples = logs.values_list("date", "weight").order_by("date")
        smoothed_date_weight_tuples = smooth_zero_weights_lerp(date_weight_tuples)
        smoothed_date_weight_tuples = smooth_zero_weights_previous_avg(
            date_weight_tuples
        )
        # Weight over Time Chart Data: timestamps, weights
        timestamps = [i[0] for i in smoothed_date_weight_tuples]
        weights = [i[1] for i in smoothed_date_weight_tuples]

        # Caloric Intake over Time Chart Data: timestamps, calories
        calories = list(logs.values_list("calories_in", flat=True).order_by("date"))

        # Handle Units
        weights = [self.handle_weight_units(i, units_weight) for i in weights]

        context.update(
            {
                "timestamps": json.dumps(
                    [date.strftime("%b-%d") for date in timestamps]
                ),
                "weights": weights,
                "calories": calories,
            }
        )

        # Check if self.request.user is friend of user
        request_user_friends_list = Friend.objects.friends(self.request.user)
        if user in request_user_friends_list:
            isFriend = True
        else:
            isFriend = False
        context.update(
            {
                "isFriend": isFriend,
            }
        )

        # Check if pending friend request
        if FriendshipRequest.objects.filter(
            from_user=self.request.user, to_user=user
        ).exists():
            # print("friendship request exists")
            isRequestedFriend = True
        else:
            isRequestedFriend = False

        context.update(
            {
                "isRequestedFriend": isRequestedFriend,
            }
        )

        # Debug print context keys and vals
        # print("\n".join("{!r}: {!r},".format(k, v) for k, v in context.items()))

        return context

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

    @staticmethod
    def get_log_rate(logs):
        # Calculate log rate as 100*(number of logs / days since first log)
        first_log_date = logs.values("date").first()
        if not first_log_date:
            return 0
        else:
            first_log_date = first_log_date["date"]
        days_since_started_logging = (
            (datetime.now(timezone.utc).date() - timedelta(days=1)) - first_log_date
        ).days

        if not (days_since_started_logging) == 0:
            return int(100 * (len(logs) / days_since_started_logging))
        else:
            return 0
