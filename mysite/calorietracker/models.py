from django.db import models
from .base_models import DateTimeFields
from django.contrib.auth import get_user_model
from safedelete.models import SafeDeleteModel
from django_measurement.models import MeasurementField
from measurement.measures import Distance, Weight


class Feedback(DateTimeFields, SafeDeleteModel):
    """docstring for Feedback."""

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    comment = models.TextField()
    contact_email = models.EmailField()


class Subscription(DateTimeFields, SafeDeleteModel):
    """docstring for Subscription."""

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

    choices = [
        ("F", "Free"),
        ("B", "Bronze"),
        ("S", "Silver"),
        ("G", "Gold"),
        ("P", "Platinum"),
    ]
    type = models.CharField(
        max_length=1, choices=choices, default="Free", blank=True, null=True
    )
    expires = models.DateTimeField(null=True, blank=True)


class Streak(DateTimeFields, SafeDeleteModel):
    """
        Represents the user streaks
    """

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)

    input_streak = models.IntegerField(
        default=0
    )  # Amount of days the user has in succession inputed data
    defecit_streak = models.IntegerField(
        default=0
    )  # Amount of days in succession that the user has a caloric defecit
    surplus_streak = models.IntegerField(
        default=0
    )  # Amount of days in succession that the user has a caloric surplus

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
      - Goal weight
      - Goal date - by when?
    """

    user = models.OneToOneField(
        get_user_model(), unique=True, blank=False, null=False, on_delete=models.CASCADE
    )

    age = models.IntegerField(blank=True, null=True)

    sex_choices = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    sex = models.CharField(max_length=1, choices=sex_choices, blank=True, null=True)
    height = MeasurementField(measurement=Distance, null=True, blank=True)
    # this should represent a range from 0 - 100 # TODO: add min max value validation

    activity_choices = [
        ("1", "Sedentary (little or no exercise)"),
        ("2", "Lightly active (light exercise/sports 1-3 days/week)"),
        ("3", "Moderatetely active (moderate exercise/sports 3-5 days/week)"),
        ("4", "Very active (hard exercise/sports 6-7 days a week)"),
        ("5", "Extra active (very hard exercise/sports & physical job or 2x training)"),
    ]
    activity = models.CharField(
        max_length=1,
        choices=activity_choices,
        blank=True,
        null=True,
        help_text="Used to estimate your total daily energy expenditure until we have enough data to calculate it",
    )

    goal_choices = [
        ("L", "Lose"),
        ("M", "Maintain"),
        ("G", "Gain"),
    ]
    goal = models.CharField(
        max_length=1,
        choices=goal_choices,
        blank=True,
        null=True,
        help_text="Do you want to lose, maintain, or gain weight?",
    )

    goal_weight = MeasurementField(measurement=Weight, null=True, blank=True)
    goal_date = models.DateTimeField(blank=True, null=True)

    unit_choices = [
        ("I", "Imperial"),
        ("M", "Metric"),
    ]
    unit_preference = models.CharField(
        max_length=1,
        choices=unit_choices,
        blank=True,
        null=True,
        help_text="Display metric or imperial units on analytics page",
    )


class Log(DateTimeFields, SafeDeleteModel):
    """
      - Date
      - Weight
      - Calories In
      - Calories Out
      - Activity LVL
    """

    user = models.ForeignKey(
        get_user_model(), blank=False, null=False, on_delete=models.CASCADE,
    )

    date = models.DateField(blank=False, unique=True)  # Log the date

    weight = MeasurementField(measurement=Weight, null=True, blank=False)

    calories_in = models.IntegerField(
        blank=False, help_text="Total calories consumed",
    )  # Calories consumed in kcal

    calories_out = models.IntegerField(
        blank=True,
        null=True,
        help_text="If you have a fitness tracker, total calories burned",
    )  # From fitness tracker e.g. apple watch, fitbit etc.

    choices = [
        ("L", "Low"),
        ("M", "Moderate"),
        ("H", "High"),
    ]

    activity_lvl = models.CharField(
        max_length=1,
        choices=choices,
        blank=True,
        null=True,
        help_text="Estimate your relative activity level",
    )
