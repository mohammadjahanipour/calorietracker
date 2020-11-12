from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from datetime import datetime, timedelta, date
import itertools, calendar

from ...models import Log
from request.models import Request


class Activity:
    def __init__(self, users, requests, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.users = users
        self.requests = requests

    @property
    def DAUs(self):
        """
        dict of {date: [unique users on date]}
        """
        day = self.start_date
        DAU_dict = {}
        while day <= self.end_date:
            DAU_dict[day] = self.unique_users_by_day(day)
            day += timedelta(days=1)
        return DAU_dict

    @property
    def DAU_counts(self):
        """
        dict of {date: number of unique users on date}
        """
        return {k: len(v) for k, v in self.DAUs.items()}

    @property
    def MAUs(self):
        """
        dict of {month: [unique users in month]}
        """
        months = list(set([i.month for i in self.DAUs.keys()]))
        MAU_dict = {}
        for month in months:
            users = {k: v for k, v in self.DAUs.items() if k.month == month}.values()
            MAU_dict[month] = list(set(itertools.chain.from_iterable(users)))

        return MAU_dict

    @property
    def MAU_counts(self):
        """
        dict of {month: number of unique users in month}
        """
        return {k: len(v) for k, v in self.MAUs.items()}
        return True

    def unique_users_by_day(self, date):
        """
        returns a list of unique users for a given date
        """
        # print("Unique users on: ", date)

        # Query all requets that occured on date
        requests_on_day = self.requests.filter(time__contains=date)

        users_on_day = []
        # If None, return empty list
        if not requests_on_day:
            unique_users_on_day = []
        else:
            # list of Users
            users_on_day = [
                i.get_user() for i in requests_on_day if i.user_id is not None
            ]

            unique_users_on_day = list(set(users_on_day))

        # print(unique_users_on_day)
        return unique_users_on_day


class Command(BaseCommand):
    help = "Calculates DAU, WAU and MAU and some other data"
    """
    Daily active users (DAU) is the total number of unique users that create any request to calorietracker.io on a given day.
    Weekly active users (WAU) is the aggregate sum of unique daily active users over a period of one week.
    Monthly active users (MAU) is the aggregate sum of unique daily active users over a period of one month.
    The ratio of DAU/MAU is typically a measure of ‘stickiness’ for internet products.
    
    Daily logs (DL) is the  total number of logs on a given day.
    Weekly logs (WL) is the aggregate sum of daily logs over a period of one week.
    Monthly logs (ML) is the aggregate sum of daily logs over a period of one month.
    The ratio of DL/ML is how 'sticky' the core functinality of calorietracker.io is.
    """

    def handle(self, *args, **options):

        users = get_user_model().objects.all()
        start_date = date(year=2020, month=10, day=12)
        today = datetime.now().date()
        response = {}
        activity = Activity(
            users=users,
            requests=Request.objects.all(),
            start_date=start_date,
            end_date=today,
        )

        # Print stuff
        DAUs = "\n".join(
            "{!r}: {!r},".format(k.strftime("%Y-%m-%d"), v)
            for k, v in activity.DAUs.items()
            if len(v) > 0
        )
        DAU_counts = "\n".join(
            "{!r}: {!r},".format(k.strftime("%Y-%m-%d"), v)
            for k, v in activity.DAU_counts.items()
        )
        MAUs = "\n".join(
            "{!r}: {!r},".format(calendar.month_abbr[k], v)
            for k, v in activity.MAUs.items()
            if len(v) > 0
        )
        MAU_counts = "\n".join(
            "{!r}: {!r},".format(calendar.month_abbr[k], v)
            for k, v in activity.MAU_counts.items()
        )
        # print("DAUs \n", DAUs)
        print("DAU Counts \n", DAU_counts)
        # print("MAUs \n", MAUs)
        print("MAU Counts \n", MAU_counts)

        print("Yesterday's DAU: ", list(activity.DAU_counts.values())[-2])
        print("Current WAU: ", sum(list(activity.DAU_counts.values())[-8:-2]))
        print("Current MAU: ", sum(list(activity.DAU_counts.values())[-32:-2]))

        self.stdout.write(self.style.SUCCESS("Calculated Active Users Sucessfully"))
