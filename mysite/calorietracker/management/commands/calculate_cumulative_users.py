from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from datetime import datetime, timedelta, date
import itertools, calendar

from ...models import Log


class UserCount:
    def __init__(self, users, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.users = users

    @property
    def daily_registered_users(self):
        """
        dict of {date: daily_registered_user_count} from start_date until end_date
        """
        daily_registered_users = {}
        day = self.start_date
        while day <= self.end_date:
            daily_registered_users[day] = self.users_registered_on_date(day)
            day += timedelta(days=1)

        return daily_registered_users

    @property
    def daily_cumulative_users(self):
        """
        dict of {date: cumulative_users_by_date} from start_date until end_date
        """
        daily_cumulative_users = {}
        cumulative_user_count = 0
        day = self.start_date
        while day <= self.end_date:
            cumulative_user_count += self.users_registered_on_date(day)
            daily_cumulative_users[day] = cumulative_user_count
            day += timedelta(days=1)

        return daily_cumulative_users

    def users_registered_on_date(self, date):
        """
        int of users registered on date
        """
        return get_user_model().objects.all().filter(date_joined__contains=date).count()


class Command(BaseCommand):
    help = "Calculates and prints daily registered and daily cumulative users"
    """
    doc
    """

    def handle(self, *args, **options):

        users = get_user_model().objects.all()
        start_date = date(year=2020, month=10, day=12)
        today = datetime.now().date()
        response = {}
        userCount = UserCount(
            users=users,
            start_date=start_date,
            end_date=today,
        )
        daily_reg_user_counts = "\n".join(
            "{!r}: {!r},".format(k.strftime("%Y-%m-%d"), v)
            for k, v in userCount.daily_registered_users.items()
        )

        print("Daily Registered Users: \n", daily_reg_user_counts)

        daily_cumulative_users_counts = "\n".join(
            "{!r}: {!r},".format(k.strftime("%Y-%m-%d"), v)
            for k, v in userCount.daily_cumulative_users.items()
        )

        print("Daily Cumulative Users: \n", daily_cumulative_users_counts)

        self.stdout.write(self.style.SUCCESS("Calculated User Count Sucessfully"))
