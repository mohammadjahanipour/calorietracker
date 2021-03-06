import djstripe
from djstripe.models import Plan, Customer
import json
import logging
from datetime import datetime, timezone
import pandas as pd

from chartjs.views.lines import BaseLineChartView
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
    TemplateView,
    UpdateView,
)
from safedelete.models import HARD_DELETE

from . import models
from .analytics_view import Analytics
from .csvimport_view import ImportCSV
from .forms import LogDataForm, LoginForm, MeasurementWidget, RegisterForm, SettingForm
from .mfpimport_views import (
    ImportMFP,
    ImportMFPCredentials,
    ImportMFPCredentialsCreate,
    ImportMFPCredentialsUpdate,
)
from .models import Feedback, Log, MFPCredentials, Setting

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe

# Get an instance of a logger
logger = logging.getLogger("PrimaryLogger")


@csrf_exempt
def my_webhook_view(request):

  payload = request.body
  event = None

  try:
    event = stripe.Event.construct_from(
      json.loads(payload), stripe.api_key
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)

  # Handle the event
  if event.type == 'payment_intent.succeeded':
    payment_intent = event.data.object  # contains a stripe.PaymentIntent
    # Then define and call a method to handle the successful payment intent.
    # handle_payment_intent_succeeded(payment_intent)
  elif event.type == 'payment_method.attached':
    payment_method = event.data.object  # contains a stripe.PaymentMethod
    # Then define and call a method to handle the successful attachment of a PaymentMethod.
    # handle_payment_method_attached(payment_method)
  # ... handle other event types
  else:
    print('Unhandled event type {}'.format(event.type))

  return HttpResponse(status=200)


class Subscription(LoginRequiredMixin, TemplateView):
    """docstring for Subscription."""

    template_name = "calorietracker/subscription.html"

    def get_context_data(self, **kwargs):

        # Create the stripe Customer, by default subscriber Model is User,
      # this can be overridden with settings.DJSTRIPE_SUBSCRIBER_MODEL
      customer, created = djstripe.models.Customer.get_or_create(subscriber=self.request.user)

      # Add the source as the customer's default card
      customer.add_card(4242424242424242)

      # Using the Stripe API, create a subscription for this customer,
      # using the customer's default payment source
      stripe_subscription = stripe.Subscription.create(
          customer=customer.id,
          items=[{"price": "price_1HajOeHK82X25fQF96b7Bbwr"}],
          collection_method="charge_automatically",
          # tax_percent=15,
          api_key=djstripe.settings.STRIPE_SECRET_KEY,
      )

      # Sync the Stripe API return data to the database,
      # this way we don't need to wait for a webhook-triggered sync
      subscription = djstripe.models.Subscription.sync_from_stripe_data(
          stripe_subscription
      )

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

    def get_form(self):
        form = super().get_form()
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
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
        self.object.delete(force_policy=HARD_DELETE)
        return HttpResponseRedirect(success_url)


class LogData(LoginRequiredMixin, CreateView):

    # TODO: check if date does not overlap with existing log

    model = Log
    form_class = LogDataForm
    template_name = "calorietracker/logdata.html"

    success_url = reverse_lazy("analytics")

    login_url = "/login/"
    redirect_field_name = "redirect_to"

    def get_form(self):
        form = super().get_form()
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


class HomePage(TemplateView):
    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)

    template_name = "calorietracker/home.html"


class Profile(TemplateView):
    template_name = "calorietracker/profile.html"


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
            messages.info(request, "You need to have made at least one log entry")
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
        login(self.request, self.object)

        # Logging
        user = self.request.user.username
        message = (
            user
            + " just registered on CalorieTracker.io! on "
            + datetime.now(timezone.utc).strftime("%A, %B %e, %Y %I:%M %p")
        )
        send_mail(
            message,
            message,
            "calorietrackerio@gmail.com",
            ["calorietrackerio@gmail.com"],
            fail_silently=False,
        )

        return super().get_success_url()


class Login(LoginView):
    form_class = LoginForm
    template_name = "calorietracker/login.html"


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
