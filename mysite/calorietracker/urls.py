from django.urls import path
from . import views
from .views import line_chart, line_chart_json


urlpatterns = [
    path("", views.Analytics.as_view(), name="home"),
    path("profile/", views.Profile.as_view(), name="profile"),
    path("logdata/", views.LogData.as_view(), name="logdata"),
    path("logs/", views.ViewLogs.as_view(), name="logs"),
    path("logdata/<pk>/edit", views.UpdateLogData.as_view(), name="UpdateLogData"),  # TODO: switch to update naming instead of edit for consistancy
    path("analytics/", views.Analytics.as_view(), name="analytics"),
    path("chartJSON", line_chart_json, name="line_chart_json"),
    # AUTH
    path("register/", views.Register.as_view(), name="register"),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("change-password/", views.PasswordChange.as_view(), name="change-password"),
    path("settings/", views.Settings.as_view(), name="settings"),
    path("feedback/", views.Feedback.as_view(), name="feedback"),

    path("import/", views.Import.as_view(), name="import"),
    path("import/credentials/mfp/", views.ImportMFPCredentials.as_view(), name="import-credentials-mfp"),
    path("import/credentials/mfp/create/", views.ImportMFPCredentialsCreate.as_view(), name="import-credentials-mfp-create"),
    path("import/credentials/mfp/update/", views.ImportMFPCredentialsUpdate.as_view(), name="import-credentials-mfp-update"),
]
