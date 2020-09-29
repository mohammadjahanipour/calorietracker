import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os


# Regression - Single Variable
def single_regression(X, Y):
    """
    Take (X, dependent variable) and (Y, independent variable)
    Predict Y from X
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
    Take (X, independent variables/features) and (Y, dependent variable)
    Predict Y from X
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
    Take (X, independent variables/features as a list of lists) and (Y, dependent variable as a list)
    Predict Y from X
    """

    ones = np.ones(len(x[0]))
    X = sm.add_constant(np.column_stack((x[0], ones)))
    for ele in x[1:]:
        X = sm.add_constant(np.column_stack((ele, X)))
    results = sm.OLS(y, X).fit()

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
    Note that using valid avoids boundary effects at start and end of array but it also returns an array of size max(x, w) - min(x, w) + 1
    """
    return np.convolve(x, np.ones(w), "valid") / w


if __name__ == "__main__":
    # Read in the data (csv for now)
    # os.path.join(os.getcwd(), "..", "sampledata.csv")
    data = pd.read_csv(os.path.join(os.getcwd(), "..", "sampledata.csv"))

    weights = pd.DataFrame(data, columns=["Weight"]).dropna()
    cal_in = pd.DataFrame(data, columns=["CI"]).dropna()
    cal_out = pd.DataFrame(data, columns=["CO"]).dropna()
    steps = pd.DataFrame(data, columns=["Steps"]).dropna()
    defecit = pd.DataFrame(data, columns=["Defecit"]).dropna()

    # # Single Regression - pretty straight forward here.
    # print("Single Regression Results for cal_in vs weights")
    # single_regression(cal_in, weights)
    # print("Single Regression Results for cal_out vs weights")
    # single_regression(cal_out, weights)
    # print("Single Regression Results for defecit vs weights")
    # single_regression(defecit, weights)
    #
    # # Scikit multiple regression - use multiple features to predict weights
    # print("Multiple Regression Results with SciKit for defecit and steps vs weights")
    # features = pd.DataFrame(data, columns=["Defecit", "Steps"]).dropna()
    # sci_multiple_regression(features, weights)
    #
    # # Statsmodels multiple regression - use multiple features to predict weights
    # # Gets more detailed summary statistics
    # features = [
    #     cal_in.to_numpy().ravel().tolist(),
    #     steps.to_numpy().ravel().tolist(),
    #     cal_out.to_numpy().ravel().tolist(),
    # ]
    # result = sm_multiple_regression(features, weights.to_numpy().ravel().tolist())
    # print(result.summary())
    #
    # # Doing it with statsmodels.formula.api is a bit easier when working with dataframes
    # #  -1 below removes the constant (y intercept)
    # df = pd.DataFrame(data, columns=["CI", "Steps", "CO", "Weight"]).dropna()
    # result = smf.ols(formula="Weight ~ CI + Steps + CO -1", data=df).fit()
    # print(result.summary())

    # TDEE Calculation; n is the last number of days to calculate TDEE for
    TDEE = calculate_TDEE(
        cal_in.to_numpy().ravel().tolist(),
        weights.to_numpy().ravel().tolist(),
        n=14,
        smooth=True,
        window=3,
    )
    print("Estimated TDEE:", TDEE)
