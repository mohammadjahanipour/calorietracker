import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
# from sklearn.linear_model import LinearRegression # removed due an error on dokku deploy
# TODO: probably remove the functions that use this and are not used anywhere anyway

from .base_models import Weight


# Regression - Single Variable
def single_regression(X, Y):
    """
    Predict Y from X using single variable regression

    Parameters
    ----------
    X : dependent variable
        {array-like, sparse matrix} of shape (n_samples, n_features)
    Y : dependent variable
        {array-like, sparse matrix} of shape (n_samples, n_features)

    Returns
    -------
    model
        Class with attributes coef_, rank, singular_, intercept_
    """

    linear_regressor = LinearRegression()  # object for the class
    model = linear_regressor.fit(X, Y)  # perform regression

    Y_pred = linear_regressor.predict(X)  # predictions
    r2 = model.score(X, Y)

    print("Intercept: \n", model.intercept_)
    print("Coefficients: \n", model.coef_)
    print("R2: \n", r2)

    return model


# Regression - Multiple Variables (scikit)
def sci_multiple_regression(X, Y):
    """
    Predict Y from X using multiple variable regression

    Parameters
    ----------
    X : dependent variables or features
        {array-like, sparse matrix} of shape (n_samples, n_features)
    Y : dependent variable
        {array-like, sparse matrix} of shape (n_samples, n_features)

    Returns
    -------
    model
        Class with attributes coef_, rank, singular_, intercept_
    """

    linear_regressor = LinearRegression()  # object for the class
    model = linear_regressor.fit(X, Y)  # perform regression
    response = model.predict(X)
    r2 = model.score(X, Y)

    print("Intercept: \n", model.intercept_)
    print("Coefficients: \n", model.coef_)
    print("R2: \n", r2)

    return model


# Regression - Multiple Variables (statsmodels)
def sm_multiple_regression(x, y):
    """
    Predict Y from X using single variable regression

    Parameters
    ----------
    X : dependent variables or features
        list of lists
    Y : dependent variable
        list

    Returns
    -------
    OLSResults
        https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.html#statsmodels.regression.linear_model.OLSResults
    """
    ones = np.ones(len(x[0]))
    X = sm.add_constant(np.column_stack((x[0], ones)))
    for ele in x[1:]:
        X = sm.add_constant(np.column_stack((ele, X)))
    results = sm.OLS(
        y, X
    ).fit()  # OLS : ordinary least squares for i.i.d. errors Σ=𝐈; Alternatives GLS, WLS, GLSAR

    return results


# TDEE Calculator
def calculate_TDEE(CI, weights, n, units="lbs", smooth=True, window=5):
    """
    Total daily energy expenditure (TDEE) is an estimate of daily caloric expenditure.
    This is a combination of one's basal metabolic rate (BMR) + numerous other factors like non-exercise activity thermogenesis, activity calories etc.
    The mathematical components of TDEE (e.g. NEAT, BMR, activity calories etc.) are considerably variable from person to person
    Thus, the best way to get aan accurate estimate of TDEE is by calculating it based on an invidual's series of weights and caloric intake

    The amount of data required to get an accurate estimate is difficult to say due to daily variations in weight secondary to water loss and GI waste
    It is also difficult to say because a person's activity level in terms of exercise and NEAT may change behaviourly over the course of long periods of time

    Thus TDEE should be constantly reevaluated using the last X days of data to give the most accurate representation.

    Here we will take a 2 inputs as np arrays: [daily calorie intakes] and [weights] over time. The length of each array is the number of days of data.
    Mathematically, calculating TDEE from this is straight forward:
        - Take the weight change from start to begining
        - Convert this weight change to calories (e.g. lbs * 3500)
        - Take the sum of daily calorie intakes
        - Take the difference betweeen the above two (i.e. total caloric intake - weight change in calories) and divide by total days
        - The result is the estimated TDEE over the last days

    The only caveat in this calculation is the day to day variability in weight affecting the total weight change calculation.
    This is counteracted by smoothing the weight over 'window' days.

    Parameters
    ----------
    CI : daily caloric intake
        list
    Weights : daily weights list
        list
    n : last number of days to calculate TDEE over
        int
    units : unit of weights
        string: "lbs" or "kgs"
    smooth : If true, will use moving_average() to smooth the daily weights, reducing day-to-day variation
        bool, default = True
    window : If smooth is true, the window over which averages will be computed
        int, default = 5 (Days)

    Returns
    -------
    TDEE
        int
    """

    # print("Daily Caloric Intake", "\n", CI)
    # print("Daily Weight Log", "\n", weights)
    # print("Number of previous days to caclulate TDEE over", "\n", n)
    # print("Are we smoothing the data?", "\n", smooth)

    if len(weights) < 3:
        return "Insufficient data"

    if smooth == True:
        # Use smoothed or EMWA weights as input or calculate them here to reduce daily variation effects. Not doing so can result in much poorer accuracy
        weights = moving_average(weights, window)

    # Trim the data so we only look at last n days.
    CI = CI[-n + 1: -2]
    weights = weights[-n:]

    #  Calculate weight change and convert to calories
    # TODO: Handle units here for pounds vs kgs
    if units == "lbs":
        delta_weight_calories = (weights[-1] - weights[0]) * 3500
    elif units == "kgs":
        delta_weight_calories = (weights[-1] - weights[0]) * 7700

    # Find difference of sum of caloric intake & raw weight lost in calories
    diff = delta_weight_calories - sum(CI)

    TDEE = diff / len(weights)

    return round(TDEE)


def calculate_HarrisBenedict(weight, sex, height, age, activity):
    # Estimate TDEE in the absence of enouhg data
    # Do all calculations in metric
    weight = weight.kg
    height = height.cm

    if sex == "M":
        BMR = round(
            -1 * float(88.362 + (13.397 * weight) +
                       (4.799 * height) - (5.677 * age)),
        )
    elif sex == "F":
        BMR = round(
            -1 * float(447.593 + (9.247 * weight) +
                       (3.098 * height) - (4.330 * age)),
        )
    if activity == "1":
        TDEE = BMR * 1.2
    elif activity == "2":
        TDEE = BMR * 1.375
    elif activity == "3":
        TDEE = BMR * 1.55
    elif activity == "4":
        TDEE = BMR * 1.725
    elif activity == "5":
        TDEE = BMR * 1.9

    return round(TDEE)


def moving_average(x, w=5):
    """
    Helper function for smoothing an array or list (x) over a window (w). Window is the number of elements over which to smooth
    Note that using "valid" avoids boundary effects at start and end of array but it also returns an array of size max(x, w) - min(x, w) + 1

    Parameters
    ----------
    x : array or list to be smoothed
        list or array
    window : dependent variable
        list

    Returns
    -------
    array
    """

    if len(x) < w:
        return x
    return np.convolve(x, np.ones(w), "valid") / w


def calculate_weight_change(weights, n, smooth=True):
    """
    Calculate change in weight.

    Parameters
    ----------
    weights : all daily weights
        array or list
    n : last number of days to calculate weight_change over
        int
    smooth : If true, will use moving_average() to smooth the daily weights, reducing day-to-day variation
        bool

    Returns
    -------
    float
    """
    if smooth:
        weights = moving_average(weights)

    weights = weights[-n:]
    return weights[-1] - weights[0]


def unit_conv(x, unit):
    """
    Converts cm to inches and vice versa
    Converts lbs to kg and vice versa

    Parameters
    ----------
    x : number to be converted
        float
    unit : current unit. Options: lbs, kgs, cm, in
        string

    Returns
    -------
    float
    """
    if unit == "lbs":
        return round(x * 0.453592, 2)
    if unit == "kgs":
        return x * 2.20462
    if unit == "in":
        return x * 2.54
    if unit == "cm":
        return x * 0.393701


def rate(x1, x2, y1, y2):
    """
    Calculate change in weight (Measurement object Weight) over change in time (Days).

    Parameters
    ----------
    x1, x2: measurement objects for which we calculate the change in weight
        Weight
    y1, y2: date objects for which we calculate the time delta in days
        datetime
    Returns
    -------
    Weight / days
    """
    # x1, x2 are measurement objects for which we calculate the change
    # y1, y2 are date objects for which we calculate the time delta in days
    weight_change = x2 - x1
    time_delta = int((y2 - y1).days)
    # print("weight_change", weight_change.lb)
    # print("time_delta", time_delta, "days")
    return weight_change / time_delta


def interpolate(x1, x2, y1, y2, y):
    """
    Linearlly interpolates a weight for day y given surrounding data points

    Parameters
    ----------
    x1, x2: measurement objects
        Weight
    y1, y2: date objects
        datetime
    y: date object between y1 and y2
        datetime
    Returns
    -------
    lerped_weight: measurment object
        Weight
    """

    slope = rate(x1, x2, y1, y2)
    days_since_x1 = int((y - y1).days)
    lerped_weight = x1 + (slope * days_since_x1)

    return lerped_weight


def smooth_zero_weights_lerp(date_weight_tuples_list):
    # weights is a list of tuples: (weight, date)
    smoothed_weights = []
    all_logs = date_weight_tuples_list  # list of tuples (date, weight)

    dates, weights = [e[0] for e in all_logs], [e[1] for e in all_logs]
    nonzeroweight_indices = [
        i for i, e in enumerate(weights) if e != Weight(g=0)]

    for i in range(len(dates)):
        if weights[i] == Weight(g=0):
            # print("index", i, "has weight 0")
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
                smoothed_weights.append(weights[i])
                continue
            else:
                interpolated_weight = interpolate(w1, w2, y1, y2, dates[i])
                smoothed_weights.append(interpolated_weight)
        else:
            smoothed_weights.append(weights[i])
    return [
        (dates[i], smoothed_weights[i]) for i in range(0, len(dates))
    ]  # list of tuples (date, weight)


def smooth_zero_weights_previous_avg(date_weight_tuples_list):
    # weights is a list of tuples: (weight, date)
    smoothed_weights = []
    all_logs = date_weight_tuples_list  # list of tuples (date, weight)

    dates, weights = [e[0] for e in all_logs], [e[1] for e in all_logs]
    n = 11

    for i in range(len(dates)):
        if weights[i] == Weight(g=0.0):
            # get last n weights
            previous = weights[i - n: i - 1]
            previous = [
                weight for weight in previous if weight != Weight(g=0.0)]
            # calculate average.
            if len((previous)):
                average = sum([value.lb for value in previous]) / len(previous)
            else:
                # if there is no elements in previous, set average to last 10 elements of nonzeroweights
                nonzeroweights = [
                    value[1].lb for value in all_logs if value[1] != Weight(g=0.0)
                ]
                if len(nonzeroweights[-10:-1]) != 0:
                    average = sum(
                        nonzeroweights[-10:-1]) / len(nonzeroweights[-10:-1])
                else:
                    average = 0
            smoothed_weights.append(Weight(lb=average))
        else:
            smoothed_weights.append(weights[i])
    return [(dates[i], smoothed_weights[i]) for i in range(0, len(dates))]


if __name__ == "__main__":
    # add path to project root dir
    sys.path.append(os.path.join(os.getcwd(), ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "mysite.settings"

    # Connect to Django ORM
    import django

    django.setup()

    from django.contrib.auth import get_user_model

    from calorietracker.models import Log, Setting

    username = "test3"
    df = pd.DataFrame(
        list(
            Log.objects.all()
            .filter(user__username=username)
            .values(
                "id",
                "created_at",
                "updated_at",
                "deleted",
                "date",
                "weight",
                "calories_in",
                "calories_out",
                "steps",
            )
        )
    )
    print(df)

    n = 102
    print("Summary Analytics for user", username, "over last", n, "days")

    TDEE = calculate_TDEE(
        df["calories_in"].tolist(),
        df["weight"].tolist(),
        n=n,
        smooth=True,
        window=3,
    )
    print("\nEstimated TDEE:", TDEE)
    weight_change_raw, weight_change_smooth = (
        weight_change(df["weight"].tolist(), n=n, smooth=False),
        weight_change(df["weight"].tolist(), n=n, smooth=True),
    )
    print("Raw Weight Change:", weight_change_raw)
    print("Smoothed Weight Change:", weight_change_smooth)
    print("Rate of Weight Change:", weight_change_smooth / n, "pounds per day")
    print("Rate of Weight Change:",
          (weight_change_smooth / n) * 7, "pounds per week")

    # # Single Regression - pretty straight forward here.
    print("\nSingle Regression Results for cal_in vs weights")
    single_regression(
        df["calories_in"].to_numpy().reshape(-1, 1),
        df["weight"].to_numpy().reshape(-1, 1),
    )
    print("\nSingle Regression Results for cal_out vs weights")
    single_regression(
        df["calories_out"].to_numpy().reshape(-1, 1),
        df["weight"].to_numpy().reshape(-1, 1),
    )

    # Scikit multiple regression - use multiple features to predict weights
    print(
        "\nMultiple Regression Results with SciKit for cal_in, cal_out, steps vs weights"
    )
    features = df[["calories_in", "calories_out", "steps"]]
    sci_multiple_regression(features, df["weight"])

    # Statsmodels multiple regression - use multiple features to predict weights
    # Gets more detailed summary statistics
    features = [
        df["calories_in"].tolist(),
        df["steps"].tolist(),
        df["calories_out"].tolist(),
    ]
    result = sm_multiple_regression(features, df["weight"].tolist())
    print(result.summary())

    # Doing it with statsmodels.formula.api is a bit easier when working with dataframes
    #  -1 below removes the constant (y intercept)
    result = smf.ols(
        formula="weight ~ calories_in + steps + calories_out -1", data=df
    ).fit()
    print(result.summary())
