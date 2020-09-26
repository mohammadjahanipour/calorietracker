from django.db import models
from . base_models import DateTimeFields
from django.contrib.auth import get_user_model
from safedelete.models import SafeDeleteModel


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
        get_user_model(), unique=True, blank=False, null=False, on_delete=models.CASCADE)

    age = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    # this should represent a range from 0 - 100 # TODO: add min max value validation
    activity = models.IntegerField(blank=True, null=True)

    goal_choices = [
        ('L', 'Lose'),
        ('M', 'Maintain'),
        ('G', 'Gain'),
        ]
    goal = models.CharField(
        max_length=2,
        choices=goal_choices,
        default='Maintain',
    )
    goal_date = models.DateTimeField(blank=True, null=True)
