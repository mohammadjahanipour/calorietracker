from datetime import datetime, timedelta, timezone

from django.views.generic import TemplateView

from ..base_models import Weight
from ..models import Log, Setting, Streak
from ..utilities import moving_average


class Profile(TemplateView):
    template_name = "calorietracker/profile.html"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        user = request.user
        # Querysets
        logs = Log.objects.all().filter(user=user).order_by("date")
        settings = Setting.objects.get(user=user)

        # Actualize input streak before querying streaks
        Streak.objects.get(user=user).actualize_input_streak()
        streaks = Streak.objects.get(user=user)

        # Context Data
        # Top row cards
        context.update(
            {
                "join_date": user.date_joined.date,
                "last_seen_date": user.last_login.date,
                "log_count": len(logs),
                "current_streak": streaks.input_streak,
                "log_rate": self.get_log_rate(logs),
            }
        )

        # Unit Handling
        current_weight = self.get_current_weight(logs)
        weight_to_go = settings.goal_weight - current_weight
        if settings.unit_preference == "M":
            units_weight = "kgs"
            current_weight = current_weight.kg
            goal_weight = settings.goal_weight.kg
            weight_to_go = weight_to_go.kg
        else:
            units_weight = "lbs"
            current_weight = current_weight.lb
            goal_weight = settings.goal_weight.lb
            weight_to_go = weight_to_go.lb

        # Goals Card data
        context.update(
            {
                "units_weight": units_weight,
                "current_weight": round(current_weight, 1),
                "weight_to_go": "{:+}".format(round(weight_to_go, 1)),
                "goal_weight": round(goal_weight, 1),
                "goal_date": settings.goal_date.strftime("%b. %-d"),
                "time_left": settings.time_to_goal(),
            }
        )

        # Logging Heatmap Data
        # todo

        # Debug print context keys and vals
        # print("\n".join("{!r}: {!r},".format(k, v) for k, v in context.items()))

        return self.render_to_response(context)

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
            current_weight = moving_average(all_nonzero_weights)[-1]
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
