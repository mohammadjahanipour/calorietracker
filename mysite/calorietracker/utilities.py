import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os, sys


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

    linear_regressor = LinearRegression()  #  object for the class
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

    linear_regressor = LinearRegression()  #  object for the class
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
def calculate_TDEE(CI, weights, n, smooth=True, window=5):
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
    smooth : If true, will use moving_average() to smooth the daily weights, reducing day-to-day variation
        bool, default = True
    window : If smooth is true, the window over which averages will be computed
        int, default = 5 (Days)

    Returns
    -------
    OLSResults
        https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.html#statsmodels.regression.linear_model.OLSResults
    """

    # print("Daily Caloric Intake", "\n", CI)
    # print("Daily Weight Log", "\n", weights)
    # print("Number of previous days to caclulate TDEE over", "\n", n)
    # print("Are we smoothing the data?", "\n", smooth)

    if smooth == True:
        # Use smoothed or EMWA weights as input or calculate them here to reduce daily variation effects. Not doing so can result in much poorer accuracy
        weights = moving_average(weights, window)

    # Trim the data so we only look at last n days.
    CI = CI[-n:]
    weights = weights[-n:]

    #  Calculate weight change and convert to calories
    # TODO: Handle units here for pounds vs kgs
    delta_weight_calories = (weights[-1] - weights[0]) * 3500

    # Find difference of sum of caloric intake & raw weight lost in calories
    diff = delta_weight_calories - sum(CI)
    TDEE = diff / n

    return TDEE


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
    return np.convolve(x, np.ones(w), "valid") / w


def weight_change(weights, n, smooth=True):
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


if __name__ == "__main__":
    sys.path.append(os.path.join(os.getcwd(), ".."))  # add path to project root dir
    os.environ["DJANGO_SETTINGS_MODULE"] = "mysite.settings"

    # Connect to Django ORM
    import django

    django.setup()

    from calorietracker.models import Log, Setting
    from django.contrib.auth import get_user_model

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
        df["calories_in"].tolist(), df["weight"].tolist(), n=n, smooth=True, window=3,
    )
    print("\nEstimated TDEE:", TDEE)
    weight_change_raw, weight_change_smooth = (
        weight_change(df["weight"].tolist(), n=n, smooth=False),
        weight_change(df["weight"].tolist(), n=n, smooth=True),
    )
    print("Raw Weight Change:", weight_change_raw)
    print("Smoothed Weight Change:", weight_change_smooth)
    print("Rate of Weight Change:", weight_change_smooth / n, "pounds per day")
    print("Rate of Weight Change:", (weight_change_smooth / n) * 7, "pounds per week")

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
