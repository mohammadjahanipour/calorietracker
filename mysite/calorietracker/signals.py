from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from .models import Streak, Setting


@receiver(post_save, sender=get_user_model())
def create_user_setting_model(sender, instance, created, **kwargs):

    if created:
        user = instance
        Setting(user=user).save()


@receiver(post_save, sender=get_user_model())
def create_user_streak_model(sender, instance, created, **kwargs):

    if created:
        user = instance
        Streak(user=user).save()


# @receiver(user_logged_in)
# def user_logged_in_sample_function(sender, request, user, **kwargs):
#     print("Example")
