import os, sys
import django
import myfitnesspal
from datetime import date, timedelta
from collections import OrderedDict

sys.path.append("")  # add path to project root dir
os.environ["DJANGO_SETTINGS_MODULE"] = "mysite.settings"

# for more sophisticated setups, if you need to change connection settings (e.g. when using django-environ):
# os.environ["DATABASE_URL"] = "postgres://myuser:mypassword@localhost:54324/mydb"

# Connect to Django ORM
django.setup()

from calorietracker.models import Log
from django.contrib.auth import get_user_model
from measurement.measures import Distance, Weight, Mass


def get_days(client, start_date, end_date=date.today() - timedelta(days=1)):
    """
    Parameters:
        client
            myfitnesspal.Client
        start_date
            datetime.date
        end_day
            datetime.date
    Returns dict of {date: objects of class day}
        day: https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py

    """

    delta = timedelta(days=1)
    output = {}
    while start_date <= end_date:
        data = client.get_date(start_date)
        output[start_date] = data
        start_date += delta

    return output


def get_weights(client, start_date, end_date):
    """
    Parameters:
        client
            myfitnesspal.Client
        start_date
            datetime.date
        end_day
            datetime.date
    Returns OrderedDict of weights
        {date: measurement}

    """
    weights_raw = client.get_measurements("Weight", start_date, end_date)
    if client.user_metadata["unit_preferences"]["weight"] == "pounds":
        weights = {k: Weight(lb=v) for k, v in weights_raw.items()}
    else:
        weights = {k: Weight(kg=v) for k, v in weights_raw.items()}

    return weights


def get_data_by_range(client, start_date, end_date=date.today() - timedelta(days=1)):
    """
    returns
    weights_dict
        OrderedDict of (datetime.date : float),
    days_dict
        dict of objects of class day
        day: https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py
    """

    weights_dict = get_weights(client, start_date=start_date, end_date=end_date)
    days_dict = get_days(client, start_date=start_date, end_date=end_date)

    return weights_dict, days_dict


def get_data_by_date(client, date):
    """
    returns
    weight
        measurement object
    day
        https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py
    """

    weight = get_weights(client, date, date)

    day = client.get_date(start_date)
    return weight, day


def merge_mfp_data(
    username,
    overwrite,
    weights_dict,
    days_dict,
    start_date,
    end_date=date.today() - timedelta(days=1),
):
    date = start_date
    while date <= end_date:
        try:
            weight = weights_dict[date]
        except KeyError:
            weight = False
        try:
            calories_in = days_dict[date].totals["calories"].C
        except KeyError:
            calories_in = False

        if not weight and not calories_in:
            # we dont add this to log
            date += timedelta(days=1)
            continue
        elif weight and not calories_in:
            # user has weight but no calories_in for date in mfp
            # todo check if the user has calories in query log
            # if not calories in query log, continue
            # if calories in query log and overwriting == True, update the query, else continue
            date += timedelta(days=1)
            continue
        elif not weight and calories_in:
            # user has no weight but has calories_in for date in mfp
            # we handle this as weight=0 now and smooth_zero_weight_logs later
            weight = Weight(lb=0.0)
        elif weight and calories_in:
            # user has weight and calories_in for date in mfp
            weight = weight

        print("Resolving date", date, "weight:", weight, "calories_in:", calories_in)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(
                    weight=weight, calories_in=calories_in
                )
                print(
                    "Overwrite is True! Updated",
                    date,
                    " entry's weight and calories_in",
                )
        else:
            print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=weight, calories_in=calories_in
            )

        date += timedelta(days=1)

    # Remove weight = 0 placeholders from above and replace with weight averages
    smooth_zero_weight_logs(
        user=get_user_model().objects.filter(username=username).all()[0]
    )


def smooth_zero_weight_logs(user):
    """
    Filters for log entries where user=user and weight=0
    Replaces these weights with the average of the last 10 entries excluding other weight=0 entries
    """

    all_weights = list(Log.objects.filter(user=user).values_list("date", "weight"))

    for i in range(len(all_weights)):
        entry = all_weights[i]
        if entry[1] == Mass(g=0.0):

            # get last 10 weights
            previous = all_weights[i - 11 : i - 1]
            # remove entries where weight is 0
            previous = [value[1] for value in previous if value[1] != Mass(g=0.0)]
            # calculate average
            average = sum([value.lb for value in previous]) / len(previous)

            # update this entry with average
            Log.objects.filter(user=user).filter(date=entry[0]).update(
                weight=Weight(lb=average)
            )


if __name__ == "__main__":
    # unit_aware is important to get measuremnt objects back for .get_date calls, but is broken for .get_measurement calls
    client = myfitnesspal.Client("user", password="pw", unit_aware=True)
    start_date = date(2020, 6, 14)

    # Get weight and MFP day object for a given date
    # print(get_data_by_date(client=client, date=start_date))

    # Get weight and MFP day object for a given date range
    # weights_dict, days_dict = get_data_by_range(client, start_date)

    # username = "mfptest25"
    # user = get_user_model()(username=username)
    # user.save()

    # Merge MFP weights_dict and days_dict into user logs
    # merge_mfp_data(
    #     username=username,
    #     overwrite=True,
    #     weights_dict=weights_dict,
    #     days_dict=days_dict,
    #     start_date=start_date,
    # )
