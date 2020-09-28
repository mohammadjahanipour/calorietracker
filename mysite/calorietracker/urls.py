from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomePage.as_view(), name="home"),
    path("profile/", views.Profile.as_view(), name="profile"),
    path("logdata/", views.LogData.as_view(), name="logdata"),
    path("charts/", views.Charts.as_view(), name="charts"),
    path("analytics/", views.Analytics.as_view(), name="analytics"),

    # AUTH
    path("register/", views.Register.as_view(), name="register"),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),

    path("settings/", views.Settings.as_view(), name="settings"),

]
