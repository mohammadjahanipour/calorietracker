import myfitnesspal
from datetime import date, timedelta
from collections import OrderedDict

from calorietracker.models import Log
from django.contrib.auth import get_user_model
from measurement.measures import Distance, Weight, Mass


def get_days_by_range(client, start_date, end_date=date.today() - timedelta(days=1)):
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


def get_weights_by_range(client, start_date, end_date=date.today() - timedelta(days=1)):
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


def get_weight_by_date(client, date):
    """
    returns
    day
        https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py
    """

    weight = get_weights_by_range(client, date, date)
    return weight


def get_day_by_date(client, date):
    """
    returns
    day
        https://github.com/coddingtonbear/python-myfitnesspal/blob/master/myfitnesspal/day.py
    """

    day = client.get_date(start_date)
    return day


def smooth_zero_weight_logs(user, method="lerp"):
    """
    Resolves/updates log entries where user=user and weight=0
    method is a string
        'previous_avg'
            Replaces these weights with the average of the last 10 entries excluding other weight=0 entries
        'lerp'
            Replace these weights with the linearlly interpolated weight using the previous nonzero weight, date and the next nonzero weight, date
            NOTE: lerp may allow weight=0 entries to remain in cases where there is no bounding nonzero weights available
    """

    if method == "previous_avg":
        all_weights = list(
            Log.objects.filter(user=user).values_list("date", "weight").order_by("date")
        )  # list of tuples (date, weight)

        for i in range(len(all_weights)):
            entry = all_weights[i]  # (date, weight)
            if entry[1] == Mass(g=0.0):
                # get last 10 weights
                previous = all_weights[i - 11 : i - 1]
                # print("previous 10 weights", previous)

                # remove entries where weight is 0
                previous = [value[1] for value in previous if value[1] != Mass(g=0.0)]
                # print("previous 10 weights without 0s", previous)

                # calculate average. if there is no elements in previous, set average to 0
                if len((previous)):
                    average = sum([value.lb for value in previous]) / len(previous)
                else:
                    average = 0

                # update this entry with average
                Log.objects.filter(user=user).filter(date=entry[0]).update(
                    weight=Weight(lb=average)
                )
                print(
                    "Updated",
                    entry[0].strftime("%m/%d/%Y"),
                    "with weight",
                    Weight(lb=average),
                )

    if method == "lerp":
        # first get all weight, dates as list of tuplesall_weights = list(
        all_logs = (
            Log.objects.filter(user=user).values_list("date", "weight").order_by("date")
        )  # list of tuples (date, weight)
        dates, weights = [e[0] for e in all_logs], [e[1] for e in all_logs]

        nonzeroweight_indices = [i for i, e in enumerate(weights) if e != Weight(g=0)]
        for i in range(len(dates)):
            if weights[i] == Weight(g=0):
                print("index", i, "has weight 0")

                # find previous date and weight that is non zero
                previous_found = next_found = False
                prev_search_index = next_search_index = i
                while prev_search_index >= 0 and previous_found == False:
                    if prev_search_index in nonzeroweight_indices:
                        w1 = weights[prev_search_index]
                        y1 = dates[prev_search_index]
                        previous_found = True
                    else:
                        prev_search_index -= 1

                # find next date and weight that is non zero
                while next_search_index < len(weights) and next_found == False:
                    if next_search_index in nonzeroweight_indices:
                        w2 = weights[next_search_index]
                        y2 = dates[next_search_index]
                        next_found = True
                    else:
                        next_search_index += 1

                if not (next_found and previous_found):
                    # print("ERROR, failed to find a valid bounding weight entry")
                    # print("next_found", next_found)
                    # print("previous_found", previous_found)
                    continue
                else:
                    interpolated_weight = interpolate(w1, w2, y1, y2, dates[i])
                    # print(w1.lb, w2.lb, y1, y2, dates[i])
                    # print("interpolated as", interpolated_weight.lb)
                    # update this entry with interpolated_weight
                    Log.objects.filter(user=user).filter(date=dates[i]).update(
                        weight=interpolated_weight
                    )
                    print(
                        "Updated",
                        dates[i].strftime("%m/%d/%Y"),
                        "with weight",
                        interpolated_weight,
                    )


def rate(x1, x2, y1, y2):
    # x1, x2 are measruement objects for which we calculate the change
    # y1, y2 are date objects for which we calculate the time delta in days
    weight_change = x2 - x1
    time_delta = int((y2 - y1).days)
    # print("weight_change", weight_change.lb)
    # print("time_delta", time_delta, "days")
    return weight_change / time_delta


def interpolate(x1, x2, y1, y2, y):

    slope = rate(x1, x2, y1, y2)
    days_since_x1 = int((y - y1).days)
    output = x1 + (slope * days_since_x1)

    return output


def merge_mfp_weights(user, overwrite, weights_dict):
    """
    Paramaters
    user:
        django user class
    overwrite: Overwrite logged weights if True
        bool
    weights_dict:
        ordered dict of date: weight
    """

    for date, weight in weights_dict.items():
        print(date, weight)
        print("Resolving date", date, "weight:", weight)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(weight=weight)
                print("Overwrite is True! Updated Weight")
        else:
            print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=weight, calories_in=0
            )  # Note we have calories_in as null=False so we place 0 and assume the user can import calories separately

    return True


def merge_mfp_calories_in(user, overwrite, days_dict):
    """
    Paramaters
    user:
        django user class
    overwrite: Overwrite logged weights if True
        bool
    days_dict
        dict of {date: objects of class day}
    """

    for date, day in days_dict.items():
        calories_in = day.totals["calories"].C
        print(date, calories_in)
        print("Resolving date", date, "calories_in:", calories_in)

        if Log.objects.filter(user=user).filter(date=date):
            if overwrite:
                Log.objects.filter(user=user).filter(date=date).update(
                    calories_in=calories_in
                )
                print("Overwrite is True! Updated calories_in")
        else:
            print("no data for date", date, "exists. Creating a new entry")
            Log.objects.create(
                user=user, date=date, weight=Weight(lb=0.0), calories_in=calories_in
            )  # Note we have weight as null=False so we place 0 and assume the user can import weights separately

    return True


if __name__ == "__main__":
    # unit_aware is important to get measuremnt objects back for .get_date calls, but is broken for .get_measurement calls
    client = myfitnesspal.Client("username", password="pw", unit_aware=True)
    start_date = date(2020, 6, 14)

    # Get weight and MFP day object for a given date
    # print(get_weight_by_date(client=client, date=start_date))
    # print(get_day_by_date(client, start_date))

    # Get weight and MFP day object for a given date range
    weights_dict = get_weights_by_range(client, start_date)
    days_dict = get_days_by_range(client, start_date)
    # print(weights_dict, "\n", days_dict)

    username = "fptest3"
    user = get_user_model()(username=username)
    user.save()
    # user = get_user_model().objects.filter(username=username).all()[0]

    # Merge dicts into logs
    merge_mfp_weights(user=user, overwrite=True, weights_dict=weights_dict)
    merge_mfp_calories_in(user=user, overwrite=True, days_dict=days_dict)

    # Handle days with weights=0.0
    # we do the lerp method which may leave some weights as 0, then we do previous avg method
    smooth_zero_weight_logs(user=user, method="lerp")
    smooth_zero_weight_logs(user=user, method="previous_avg")

    # lerping method helpers
    # w1 = Weight(lb=205)
    # y1 = date(2020, 10, 13)
    # w2 = Weight(lb=200)
    # y2 = date(2020, 10, 18)
    # y = date(2020, 10, 14)
    # print(w1, w2, y1, y2, y)
    # print("lerped", interpolate(w1, w2, y1, y2, y).lb)

    # Handle days wtih calories_in = 0.0