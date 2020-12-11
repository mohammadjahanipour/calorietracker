from actstream import action
import json
import logging
from datetime import datetime, timezone
import pandas as pd

from chartjs.views.lines import BaseLineChartView
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from friendship.models import Block, Follow, Friend, FriendshipRequest
from measurement.measures import Weight
from safedelete.models import HARD_DELETE

from .. import models
from ..forms import (
    FriendForm,
    FriendShipRequestForm,
    LogDataForm,
    LoginForm,
    MeasurementWidget,
    RegisterForm,
    SettingForm,
)
from ..models import Feedback, Log, MFPCredentials, Setting

# Get an instance of a logger
logger = logging.getLogger("PrimaryLogger")


class SendFriendRequest(LoginRequiredMixin, FormView):
    """docstring for AcceptFriend."""

    form_class = FriendShipRequestForm
    success_url = "/contacts/"

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.

        to_user = form.cleaned_data.get("to_user")

        Friend.objects.add_friend(
            self.request.user,  # The sender
            to_user,  # The recipient
            message="Hi! I would like to add you",
        )  # This message is optional

        # Creating a notification for the recipient
        action.send(self.request.user,
                    verb=f"Friend Request from {to_user.username}", target=to_user)

        messages.success(self.request, "Friend Request Sent")

        return super().form_valid(form)


class RemoveFriend(LoginRequiredMixin, FormView):
    """docstring for RemoveFriend."""

    # Removes an existing aka previously accepted friend

    form_class = FriendForm
    success_url = "/contacts/"

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.

        from_user = form.cleaned_data.get("from_user")
        # Remove friend request
        Friend.objects.remove_friend(self.request.user, from_user)

        messages.info(self.request, "Friend Removed")

        return super().form_valid(form)


class RejectFriend(LoginRequiredMixin, FormView):
    """Rejects a friend request not to be confused with removing a existing friend"""

    form_class = FriendForm
    success_url = "/contacts/"

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.

        from_user = form.cleaned_data.get("from_user")
        # Reject friend request
        friend_request = FriendshipRequest.objects.get(
            to_user=self.request.user, from_user=from_user
        )
        friend_request.reject()

        messages.info(self.request, "Friend Request Rejected")

        return super().form_valid(form)


class AcceptFriend(LoginRequiredMixin, FormView):
    """docstring for AcceptFriend."""

    form_class = FriendForm
    success_url = "/contacts/"

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.

        from_user = form.cleaned_data.get("from_user")
        # Accept friend request
        friend_request = FriendshipRequest.objects.get(
            to_user=self.request.user, from_user=from_user
        )
        friend_request.accept()

        messages.success(self.request, "Friend Request Accepted")

        return super().form_valid(form)


class Contacts(LoginRequiredMixin, TemplateView):
    """"""

    # The forms for this view/template are built manually in the template

    # TODO: find out if friendships go both ways seems not to
    # OPTIMIZE: refreshing the page causes the state to be lost in the tabs

    template_name = "calorietracker/contacts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_friends"] = Friend.objects.friends(self.request.user)
        context["unrejected_friend_requests"] = Friend.objects.unrejected_requests(
            user=self.request.user
        )
        context["pending_friends_count"] = len(
            context["unrejected_friend_requests"]
        )

        return context

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)


class Subscription(LoginRequiredMixin, TemplateView):
    """docstring for Subscription."""

    template_name = "calorietracker/subscription.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class Referral(LoginRequiredMixin, TemplateView):
    """docstring for Referral."""

    template_name = "calorietracker/referral.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        referral = models.Referral.create(
            user=self.request.user, redirect_to=reverse_lazy("settings")
        )

        context["referral"] = referral
        return context


class Feedback(LoginRequiredMixin, CreateView):
    """docstring for Feedback."""

    model = Feedback
    fields = (
        "comment",
        "contact_email",
    )

    success_url = reverse_lazy("feedback")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Feedback Submited")
        return super().form_valid(form)


class UpdateLogData(LoginRequiredMixin, UpdateView):
    """docstring for UpdateLogData."""

    # TODO: check if date does not overlap with existing log
    model = Log
    form_class = LogDataForm
    template_name = "calorietracker/update_logdata.html"

    success_url = reverse_lazy("analytics")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def get_queryset(self):
        return Log.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_form(self):
        form = super().get_form()
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()

        # Re-actualize input streak
        self.request.user.streak.actualize_input_streak()
        return super().form_valid(form)


class DeleteLogData(LoginRequiredMixin, DeleteView):
    model = Log
    success_url = reverse_lazy("logs")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def get_queryset(self):
        return Log.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Delete Log without SAFE_DELETE
        self.object.delete(force_policy=HARD_DELETE)

        # Re-actualize input streak
        self.request.user.streak.actualize_input_streak()

        return HttpResponseRedirect(success_url)


class LogData(LoginRequiredMixin, CreateView):

    model = Log
    form_class = LogDataForm
    template_name = "calorietracker/logdata.html"

    success_url = reverse_lazy("analytics")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def get_form(self):
        form = super().get_form()

        # We can initialize fields here as needed
        user_weight_units = Setting.objects.get(
            user=self.request.user).unit_preference
        if user_weight_units == "M":
            # Show metric units first
            form["weight"].field.widget.widgets[1].choices = [
                ("kg", "kgs"),
                ("lb", "lbs"),
            ]
        else:
            # Show imperial units first
            form["weight"].field.widget.widgets[1].choices = [
                ("lb", "lbs"),
                ("kg", "kgs"),
            ]

        # Default the date to today
        form.initial["date"] = datetime.today()

        return form

    def form_valid(self, form):
        form.instance.user = self.request.user

        query_set = Log.objects.filter(user=self.request.user).filter(
            date=form.cleaned_data.get("date")
        )
        if query_set:
            pk = str(
                (
                    Log.objects.filter(user=self.request.user)
                    .filter(date=form.cleaned_data.get("date"))
                    .values_list("id", flat=True)
                )[0]
            )
            messages.warning(
                self.request,
                mark_safe(
                    "A log for "
                    + str(form.cleaned_data.get("date"))
                    + " already exists. You can update <a href='/logdata/"
                    + pk
                    + "/update'>this entry here</a>"
                ),
            )
            return super().form_invalid(form)

        if self.request.method == "POST":
            form.save()

            # Re-actualize input streak
            self.request.user.streak.actualize_input_streak()
        return super().form_valid(form)


class Settings(LoginRequiredMixin, UpdateView):

    # TODO: do rounding on outputed height

    model = Setting
    form_class = SettingForm

    template_name = "calorietracker/settings.html"

    success_url = reverse_lazy("settings")

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.setting

    def get_form(self):
        form = super().get_form()
        return form


class ViewLogs(TemplateView):
    template_name = "calorietracker/logstable.html"

    def load_data(self, **kwargs):
        self.query_set = (
            Log.objects.all()
            .filter(user=self.request.user)
            .values("id", "date", "weight", "calories_in")
            .order_by("date")
        )
        df_query = pd.DataFrame(list(self.query_set))
        settings_set = Setting.objects.all().filter(user=self.request.user).values()
        df_settings = pd.DataFrame(list(settings_set))

        self.units = df_settings["unit_preference"].all()

        # weights, calories_in, dates
        self.rawweights = df_query["weight"].tolist()
        self.weights = df_query["weight"].tolist()
        self.weights = [round(x.lb, 2) for x in self.weights]
        self.calories_in = df_query["calories_in"].tolist()
        self.dates = df_query["date"].tolist()
        self.ids = df_query["id"].tolist()

        # Unit control
        # NOTE: all initial calculations above are done in imperial.
        # We convert to metric as needed at the very end here.
        if self.units == "I":
            self.unitsweight = "lbs"
        elif self.units == "M":
            self.unitsweight = "kgs"
            self.weights = [round(x.kg, 2) for x in self.rawweights]

        self.logtabledata = self.get_logtabledata()

    def dispatch(self, request):

        if not self.request.user.is_authenticated:
            return redirect(reverse_lazy("login"))
        if not Log.objects.filter(user=self.request.user).exists():
            messages.info(
                request, "You need to have made at least one log entry")
            return redirect(reverse_lazy("logdata"))

        return super().dispatch(request)

    def get_logtabledata(self):
        logtabledata = []
        for i in range(len(self.weights)):
            entry = {}
            entry["id"] = self.ids[i]
            entry["date"] = self.dates[i]
            entry["weight"] = self.weights[i]
            entry["calories_in"] = self.calories_in[i]
            logtabledata.append(entry)
        return logtabledata

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.load_data()

        context = {
            "units": self.units,
            "units_weight": self.unitsweight,
            "logjson_data": json.dumps(
                {"data": self.logtabledata},
                sort_keys=True,
                indent=1,
                cls=DjangoJSONEncoder,
            ),
        }
        return context


class LineChartJSONView(BaseLineChartView):
    pass


class Register(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy("settings")
    template_name = "calorietracker/register.html"

    def form_valid(self, form):
        # flash message assumes that the registration view redirects directly to a relavent page or that the flash message wont be retrieved in the login view
        messages.info(
            self.request,
            "Predictions will be inaccurate until you update your settings",
        )

        return super().form_valid(form)

    def get_success_url(self):

        # Log user in so he can be redirect to the settings page without having to login manually
        login(self.request, self.object, settings.AUTHENTICATION_BACKENDS[0])

        # # Logging
        # user = self.request.user.username
        # message = (
        #     user
        #     + " just registered on CalorieTracker.io! on "
        #     + datetime.now(timezone.utc).strftime("%A, %B %e, %Y %I:%M %p")
        # )
        # send_mail(
        #     message,
        #     message,
        #     "calorietrackerio@gmail.com",
        #     ["calorietrackerio@gmail.com"],
        #     fail_silently=False,
        # )

        return super().get_success_url()


# Deprecated in favor of AllAuthLogin
# class Login(LoginView):
#     form_class = LoginForm
#     template_name = "calorietracker/login.html"


class Logout(LogoutView):
    """Logout"""


class PasswordChange(PasswordChangeView):
    """PasswordChange"""

    success_url = reverse_lazy("home")
    template_name = "calorietracker/change-password.html"


class Purchase(LoginRequiredMixin):
    """docstring for Purchase."""


class PrivacyPolicy(TemplateView):
    template_name = "calorietracker/privacy-policy.html"


class Terms(TemplateView):
    template_name = "calorietracker/terms-and-conditions.html"


class LandingPage(TemplateView):

    template_name = "calorietracker/home.html"

    def dispatch(self, request):
        """"""

        # Redirect loged in users to their analytics page instead of the landing page
        if self.request.user.is_authenticated:

            # cant redirect to analytics page because user has no logs
            if request.user.log_set.count() == 0:
                return redirect(reverse_lazy("logdata"))

            return redirect(reverse_lazy("analytics"))
        return super().dispatch(request)
