from django.urls import path

from . import views

urlpatterns = [
    path("", views.Analytics.as_view(), name="home"),
    path("profile/", views.Profile.as_view(), name="profile"),
    path("logdata/", views.LogData.as_view(), name="logdata"),
    path("logs/", views.ViewLogs.as_view(), name="logs"),
    path("logdata/<pk>/update/", views.UpdateLogData.as_view(), name="UpdateLogData"),
    path("logdata/<pk>/delete/", views.DeleteLogData.as_view(), name="DeleteLogData"),
    path("analytics/", views.Analytics.as_view(), name="analytics"),
    # AUTH
    path("register/", views.Register.as_view(), name="register"),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.Logout.as_view(), name="logout"),
    path("change-password/", views.PasswordChange.as_view(), name="change-password"),
    path("settings/", views.Settings.as_view(), name="settings"),
    path("feedback/", views.Feedback.as_view(), name="feedback"),
    # IMPORT
    path("import/csv", views.ImportCSV.as_view(), name="importcsv"),
    path("import/mfp", views.ImportMFP.as_view(), name="importmfp"),
    path(
        "import/credentials/mfp/",
        views.ImportMFPCredentials.as_view(),
        name="import-credentials-mfp",
    ),
    path(
        "import/credentials/mfp/create/",
        views.ImportMFPCredentialsCreate.as_view(),
        name="import-credentials-mfp-create",
    ),
    path(
        "import/credentials/mfp/update/",
        views.ImportMFPCredentialsUpdate.as_view(),
        name="import-credentials-mfp-update",
    ),
    path("referral-program/", views.Referral.as_view(), name="referral-program"),
    path("privacy-policy/", views.PrivacyPolicy.as_view(), name="privacy-policy"),
    path("subscription/", views.Subscription.as_view(), name="subscription"),
]
