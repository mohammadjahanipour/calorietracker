import os, sys
import django
import datetime
import pandas as pd

sys.path.append("")  # add path to project root dir
os.environ["DJANGO_SETTINGS_MODULE"] = "mysite.settings"

# for more sophisticated setups, if you need to change connection settings (e.g. when using django-environ):
# os.environ["DATABASE_URL"] = "postgres://myuser:mypassword@localhost:54324/mydb"

# Connect to Django ORM
django.setup()

from calorietracker.models import Log
from django.contrib.auth import get_user_model
from measurement.measures import Distance, Weight

data = pd.read_csv("sampledata.csv")

username = "test3"
user = get_user_model()(username=username)
user.save()

df = pd.DataFrame(data, columns=["Date", "Weight", "CO", "CI", "Steps"]).dropna()
df["Date"] = df["Date"].apply(
    lambda x: datetime.datetime.strptime(x, "%d-%b").replace(year=2020)
)
df["Date"] = df["Date"].apply(lambda x: x.strftime("%Y-%m-%d"))

for index, row in df.iterrows():
    Log.objects.create(
        user=user,
        date=row["Date"],
        weight=Weight(lb=row["Weight"]),
        calories_in=row["CI"],
        calories_out=row["CO"],
    )
