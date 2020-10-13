from django.urls import path
from . import views
from .views import line_chart, line_chart_json


urlpatterns = [
    path("", views.Analytics.as_view(), name="home"),
    path("profile/", views.Profile.as_view(), name="profile"),
    path("logdata/", views.LogData.as_view(), name="logdata"),
    path("logs/", views.ViewLogs.as_view(), name="logs"),
    path("import/", views.Import.as_view(), name="import"),
    path("logdata/<pk>/edit", views.UpdateLogData.as_view(), name="UpdateLogData"),
    path("analytics/", views.Analytics.as_view(), name="analytics"),
    path("chartJSON", line_chart_json, name="line_chart_json"),
    # AUTH
    path("register/", views.Register.as_view(), name="register"),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("change-password/", views.PasswordChange.as_view(), name="change-password"),
    path("settings/", views.Settings.as_view(), name="settings"),
    path("feedback/", views.Feedback.as_view(), name="feedback"),
]
