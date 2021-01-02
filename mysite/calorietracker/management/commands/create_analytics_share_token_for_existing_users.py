from django.core.management.base import BaseCommand, CommandError


from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model

from ...models import AnalyticsShareToken


class Command(BaseCommand):
    help = "Creates share tokens that do not already exists"

    def handle(self, *args, **options):

        users = get_user_model().objects.all()

        for user in users:

            try:
                # user has already a share token
                user.analyticssharetoken

            except ObjectDoesNotExist:
                AnalyticsShareToken(user=user).save()

        self.stdout.write(
            self.style.SUCCESS("Share Tokens Created Much success very noice")
        )
