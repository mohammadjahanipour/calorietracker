from django.db import models
from .base_models import DateTimeFields
from django.contrib.auth import get_user_model
from safedelete.models import SafeDeleteModel


class Streak(DateTimeFields, SafeDeleteModel):
    """
        Represents the user streaks
    """

    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE
    )

    input_streak = models.IntegerField(default=0)  # Amount of days the user has in succession inputed data
    defecit_streak = models.IntegerField(default=0)  # Amount of days in succession that the user has a caloric defecit
    surplus_streak = models.IntegerField(default=0)  # Amount of days in succession that the user has a caloric surplus

    def actualize_input_streak(self):
        """
        Actualizes the input streak via counting the consecutive log entries
        """

        logs = self.user.log_set.all().order_by("date")
        streak = 0
        last_log = None

        for log in logs:
            print(log.date)

            if last_log is None:
                last_log = log
                continue

            if (log.date - last_log.date).days <= 1:
                streak += 1
            else:
                streak = 0

            last_log = log

        self.input_streak = streak
        self.save()


class Setting(DateTimeFields, SafeDeleteModel):
    """
      - Age
      - Sex/gender
      - Height
      - Perceived activity level
      - Goal - maintain, lose, gain
      - Goal date - by when?
      - *Goal per week - caloric deficit/surprlus/goal for week, pounds per week ** not yet implemented
    """

    user = models.OneToOneField(
        get_user_model(), unique=True, blank=False, null=False, on_delete=models.CASCADE
    )

    age = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    # this should represent a range from 0 - 100 # TODO: add min max value validation
    activity = models.IntegerField(blank=True, null=True)

    goal_choices = [
        ("L", "Lose"),
        ("M", "Maintain"),
        ("G", "Gain"),
    ]
    goal = models.CharField(max_length=1, choices=goal_choices, blank=True, null=True)
    goal_date = models.DateTimeField(blank=True, null=True)


class Log(DateTimeFields, SafeDeleteModel):
    """
      - Date
      - Weight
      - Calories In
      - Exercise time
      - Exercise Minutes
      - Steps
      - Calories Out
    """

    user = models.ForeignKey(
        get_user_model(), blank=False, null=False, on_delete=models.CASCADE,
    )

    date = models.DateField()  # Log the date
    weight = models.FloatField()  # TODO: Handle unit conversion kg vs lbs
    calories_in = models.IntegerField()  # Calories consumed in kcal

    exercise_choices = [
        ("C", "Cardio"),
        ("ST", "Strength"),
        ("O", "Other"),
    ]
    exercise_time = models.IntegerField(null=True)  # Time spent exercising
    exercise_type = models.CharField(choices=exercise_choices, max_length=20, null=True)

    steps = models.IntegerField(null=True)  # From fitness tracker or phone

    calories_out = models.IntegerField(
        null=True
    )  # From fitness tracker e.g. apple watch, fitbit etc.
