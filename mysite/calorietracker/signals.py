from actstream import action
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Setting, Streak, Wallet, AnalyticsShareToken
from pinax.referrals.models import Referral, ReferralResponse
from pinax.referrals.signals import user_linked_to_response


@receiver(user_linked_to_response)
def handle_user_linked_to_response_credit_referrer(sender, response, **kwargs):
    # credits the referer with 10 coins

    if response.action == "RESPONDED":

        # only credit one Response otherwise social logins via a ref link will be credited repeatedly
        count = ReferralResponse.objects.filter(user=response.user).count()
        if count >= 2:
            return

        referrer = response.referral.user
        Wallet.objects.update_or_create(user=referrer)  # create wallet if not exists
        referrer.wallet.coins += 10
        referrer.wallet.save()


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


@receiver(post_save, sender=get_user_model())
def create_user_analytics_share_token(sender, instance, created, **kwargs):

    # uuid token is automatically created by default in the model
    if created:
        user = instance
        AnalyticsShareToken(user=user).save()


@receiver(user_logged_in)
def actualize_streaks(sender, request, user, **kwargs):
    # Actualize user's input streak
    user.streak.actualize_input_streak()


# Action example
# @receiver(post_save, sender=Setting)
# def my_handler(sender, instance, created, **kwargs):
#     action.send(instance, verb='was saved')
