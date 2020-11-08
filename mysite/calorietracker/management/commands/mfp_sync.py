from datetime import date, datetime, timedelta, timezone
import myfitnesspal

from django.core.management.base import BaseCommand, CommandError

from ... import views
from ...models import MFPCredentials


def auto_sync_MFP(user, start_date, client):
    start_date = start_date.replace(tzinfo=timezone.utc).date()
    end_date = datetime.today().replace(tzinfo=timezone.utc).date()

    weights_dict = views.get_weights_by_range(
        client=client, start_date=start_date, end_date=end_date
    )
    views.merge_mfp_weights(
        user=user,
        overwrite=False,
        weights_dict=weights_dict,
    )

    days_dict = views.get_days_by_range(
        client=client, start_date=start_date, end_date=end_date
    )
    views.merge_mfp_calories_in(
        user=user,
        overwrite=False,
        days_dict=days_dict,
    )


class Command(BaseCommand):
    help = "Syncs MFP Data to our DB"

    def handle(self, *args, **options):
        # First get users who have MFP credentials + MFPautosync on
        autosync_on_queryset = MFPCredentials.objects.filter(mfp_autosync=True)

        # Iterate throguh these entries
        for i in autosync_on_queryset:
            print("Running MFP auto_sync for", i.user)

            try:
                client = myfitnesspal.Client(
                    username=i.username,
                    password=i.password,
                    unit_aware=True,
                )
                print("Succesfully logged into mfp client for", i.user)
            except myfitnesspal.exceptions.MyfitnesspalLoginError:
                print("Credential login error for", i.user)
                continue

            # Update their weights, calories in using auto_sync_helper
            auto_sync_MFP(
                user=i.user, start_date=i.mfp_autosync_startdate, client=client
            )

        success_msg = (
            "Completed MFP AutoSync for " + str(len(autosync_on_queryset)) + " users"
        )

        self.stdout.write(self.style.SUCCESS(success_msg))
