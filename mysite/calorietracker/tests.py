from datetime import datetime, date

import pandas as pd
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse_lazy
from measurement.measures import Distance, Weight

from .models import Log, Streak


# Test Urls Status Codes
# Note we only test for 200 response codes
# We do not test for functionality here other than login validation
class UrlsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        data = pd.read_csv("sampledata.csv")

        username = "test3"
        user = User.objects.create(username=username)
        user.set_password("test")
        user.save()

        df = pd.DataFrame(
            data, columns=["Date", "Weight", "CO", "CI", "Steps"]
        ).dropna()
        df["Date"] = df["Date"].apply(
            lambda x: datetime.strptime(x, "%d-%b").replace(year=2020)
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

    def test_login(self):
        print("Url: test_login")
        self.assertFalse(self.client.login(username="test3", password="wrongpw"))
        self.assertTrue(self.client.login(username="test3", password="test"))

    def test_logdata_response(self):
        print("Url: test_logdata_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("logdata"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_logs_response(self):
        print("Url: test_logs_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("logs"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_analytics_response(self):
        print("Url: test_analytics_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("analytics"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_change_password_response(self):
        print("Url: test_change_password_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("change-password"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_settings_response(self):
        print("Url: test_settings_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("settings"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_feedback_response(self):
        print("Url: test_feedback_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("feedback"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_importcsv_response(self):
        print("Url: test_importcsv_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("importcsv"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_importmfp_response(self):
        print("Url: test_importmfp_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("importmfp"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_import_credentials_mfp_response(self):
        print("Url: test_import_credentials_mfp_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("import-credentials-mfp"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_referral_program_response(self):
        print("Url: test_referral_program_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("referral-program"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_response(self):
        print("Url: test_privacy_policy_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("privacy-policy"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_subscription_response(self):
        print("Url: test_subscription_response")
        self.client.login(username="test3", password="test")
        response = self.client.get(reverse_lazy("subscription"), follow=True)
        self.assertEqual(response.status_code, 200)


# Test Models
# Tested models: Log
# Untested models: MFPCredentials, Feedback, Subscription, Streak, Setting,
class LogModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        data = pd.read_csv("sampledata.csv")
        username = "test3"
        user = get_user_model()(username=username)
        user.save()
        df = pd.DataFrame(
            data, columns=["Date", "Weight", "CO", "CI", "Steps"]
        ).dropna()

        df["Date"] = df["Date"].apply(
            lambda x: datetime.strptime(x, "%d-%b").replace(year=2020)
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

    def test_unique_constraint(self):
        # test unique_together = ("user", "date")
        print("LogModelTest Method: test_unique_constraint")
        username = "test3"

        def duplicate_Log():
            try:
                Log.objects.create(
                    user=get_user_model().objects.filter(username=username).all()[0],
                    date=datetime(2020, 9, 23),
                    weight=Weight(lb=200),
                    calories_in=2000,
                )
                self.fail("Unique constraint - unique together [user, date] failed")
            except IntegrityError:
                return IntegrityError

        self.assertEqual(IntegrityError, duplicate_Log())

    def test_null_constraint_Log_date(self):
        print("LogModelTest Method: test_null_constraint_Log_date")
        username = "test3"
        user = get_user_model().objects.filter(username=username).all()[0]
        try:
            Log.objects.create(
                user=user,
                date=None,
                weight=Weight(lb=200),
                calories_in=2000,
            )
            self.fail("Null constraint Log.date failed")
        except IntegrityError:
            result = IntegrityError
        self.assertEqual(IntegrityError, result)

    def test_null_constraint_Log_calories_in(self):
        print("LogModelTest Method: test_null_constraint_Log_calories_in")
        username = "test3"
        user = get_user_model().objects.filter(username=username).all()[0]
        try:
            Log.objects.create(
                user=user,
                date=datetime(2021, 10, 23),
                weight=Weight(lb=200),
                calories_in=None,
            )
            self.fail("Null constraint Log.calories_in failed")
        except IntegrityError:
            result = IntegrityError
        self.assertEqual(IntegrityError, result)


# Test Forms
# Tested forms: RegisterForm, LoginForm, LogDataForm
# Untested forms: Progresspic in LogDataForm, ImportCSVForm, ImportMFPForm, SettingForm
# todo
class FormTests(TestCase):
    def setUp(self) -> None:
        self.username = "testuser"
        self.email = "testuser@email.com"
        self.password = "testpw"

    def test_register_form_response(self):
        print("FormTests: test_register_form_response")
        response = self.client.get(reverse_lazy("register"))
        self.assertEqual(response.status_code, 200)

    def test_register_form_registration(self):
        print("FormTests: test_register_form_registration")
        response = self.client.post(
            reverse_lazy("register"),
            data={
                "username": self.username,
                "email": self.email,
                "password1": self.password,
                "password2": self.password,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        users = get_user_model().objects.all()
        self.assertEqual(users.count(), 1)

    def test_login_form(self):
        print("FormTests: test_login_form_login")
        response = self.client.post(
            reverse_lazy("login"),
            data={"username": self.username, "password": self.password},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_logdata_form(self):
        print("FormTests: test_logdata_form_logdata")
        self.client.force_login(User.objects.get_or_create(username="formtests")[0])
        response = self.client.post(
            reverse_lazy("logdata"),
            data={
                "date": date(2019, 4, 13),
                "weight_0": 200,
                "weight_1": "lb",
                "calories_in": 2000,
                "calories_out": 1000,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        logs = Log.objects.all()
        print(logs)
        self.assertEqual(logs.count(), 1)


# Test Views
# todo
