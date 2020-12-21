import debug_toolbar
from allauth.account.views import LoginView as AllAuthLoginView
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.LandingPage.as_view(), name="welcome"),
    path("home/", views.LandingPage.as_view(), name="home"),
    path("profile/", views.Profile.as_view(), name="profile"),
    path("profile/<slug:slug>", views.Profile.as_view(), name="profile"),
    path("logdata/", views.LogData.as_view(), name="logdata"),
    path("logs/", views.ViewLogs.as_view(), name="logs"),
    path("logdata/<pk>/update/", views.UpdateLogData.as_view(), name="UpdateLogData"),
    path("logdata/<pk>/delete/", views.DeleteLogData.as_view(), name="DeleteLogData"),
    path("analytics/<uuid>/", views.Analytics.as_view(), name="analytics"),
    path("analytics/", views.Analytics.as_view(), name="analytics"),
    # AUTH
    path("register/", views.Register.as_view(), name="register"),
    path("login/", AllAuthLoginView.as_view(), name="login"),
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
    # CONTACTS / FRIENDSHIP / COACH-CLIENT
    path("contacts/", views.Contacts.as_view(), name="contacts"),
    path("clients/", views.Clients.as_view(), name="clients"),
    path("accept-friend/", views.AcceptFriend.as_view(), name="acceptfriend"),
    path("reject-friend/", views.RejectFriend.as_view(), name="rejectfriend"),
    path("remove-friend/", views.RemoveFriend.as_view(), name="removefriend"),
    path(
        "send-friend-request/",
        views.SendFriendRequest.as_view(),
        name="sendfriendrequest",
    ),
    path(
        "cancel-friend-request/",
        views.CancelFriendRequest.as_view(),
        name="cancelfriendrequest",
    ),
    path(
        "add-coach/",
        views.AddCoach.as_view(),
        name="addcoach",
    ),
    path(
        "add-client/",
        views.AddClient.as_view(),
        name="addclient",
    ),
    path(
        "remove-coach-client/",
        views.RemoveCoachClient.as_view(),
        name="removecoachclient",
    ),
    # MISC
    path("referral-program/", views.Referral.as_view(), name="referral-program"),
    path("privacy-policy/", views.PrivacyPolicy.as_view(), name="privacy-policy"),
    path("subscription/", views.Subscription.as_view(), name="subscription"),
    path("terms-and-conditions/", views.Terms.as_view(), name="terms-and-conditions"),
]

if settings.DEBUG:

    # Test Sentry error reporting
    def trigger_error(request):
        division_by_zero = 1 / 0

    urlpatterns.append(path("sentry-debug/", trigger_error))
