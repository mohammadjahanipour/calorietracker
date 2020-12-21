import json

from actstream import action
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.views.generic import FormView, TemplateView
from friendship.models import Block, Follow, Friend, FriendshipRequest

from ..forms import (
    FriendForm,
    FriendShipRequestForm,
    LogDataForm,
    LoginForm,
    MeasurementWidget,
    RegisterForm,
    SettingForm,
)
from ..models import CoachClient
from .profile import Profile


class SendFriendRequest(LoginRequiredMixin, FormView):
    """docstring for SendFriendRequest."""

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
        action.send(
            self.request.user,
            verb=f"Friend Request from {self.request.user.username}",
            target=to_user,
        )

        messages.success(self.request, "Friend Request Sent")

        return super().form_valid(form)


class CancelFriendRequest(LoginRequiredMixin, FormView):
    """docstring for CancelFriendRequest."""

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
        print("to_user", (to_user))

        friend_request = FriendshipRequest.objects.get(
            from_user=self.request.user, to_user=to_user
        )
        friend_request.cancel()

        # Todo check if the action signal is succesfully being deleted
        # this is a known issue with a simple fix: https://github.com/revsys/django-friendship/issues/123

        messages.success(self.request, "Friend Request Canceled")

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

        # Creating a notification for the request from_user
        action.send(
            self.request.user,
            verb=f"You are now friends with {self.request.user.username}! You can view all your friends in the client tab.",
            target=from_user,
        )

        messages.success(self.request, "Friend Request Accepted")

        return super().form_valid(form)


class Contacts(LoginRequiredMixin, TemplateView):
    """docstring for Contacts."""

    # todo OPTIMIZE: refreshing the page causes the state to be lost in the tabs

    template_name = "calorietracker/contacts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_friends"] = Friend.objects.friends(self.request.user)
        context["unrejected_friend_requests"] = Friend.objects.unrejected_requests(
            user=self.request.user
        )

        context["pending_outgoing_requests"] = Friend.objects.sent_requests(
            user=self.request.user
        )

        context["pending_friends_count"] = len(
            context["unrejected_friend_requests"]
        ) + len(context["pending_outgoing_requests"])

        # Coach Role Relations to user
        context["coaches"] = [
            coachclient.coach
            for coachclient in CoachClient.objects.filter(client=self.request.user)
        ]

        context["clients"] = [
            coachclient.client
            for coachclient in CoachClient.objects.filter(coach=self.request.user)
        ]

        return context

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)


class Clients(LoginRequiredMixin, TemplateView):
    """docstring for Clients."""

    # todo OPTIMIZE: refreshing the page causes the state to be lost in the tabs

    template_name = "calorietracker/clients.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Unit Preference
        unit_preference = self.request.user.setting.unit_preference
        if unit_preference == "M":
            weights_label = "kgs"
        else:
            weights_label = "lbs"

        coach_clients_qs = CoachClient.objects.filter(coach=self.request.user)

        # for each client we create an object containing Name, Current Weight, Goal Weight, Goal Date, Logging Rate
        # and append it to clients list to later be serialized
        clients = []
        for i in coach_clients_qs:
            client_data = {}
            client_data["Name"] = i.client.username
            logs = i.client.log_set.all().order_by("date")
            current_weight = Profile.get_current_weight(logs)
            client_data["Current Weight"] = round(
                (current_weight.kg if unit_preference == "M" else current_weight.lb), 1
            )
            client_data["Goal Date"] = i.client.setting.goal_date.strftime("%b. %-d")
            goal_weight = i.client.setting.goal_weight
            client_data["Goal Weight"] = round(
                (goal_weight.kg if unit_preference == "M" else goal_weight.lb), 1
            )
            client_data["Log Rate"] = Profile.get_log_rate(logs)
            client_data["uuid"] = i.client.analyticssharetoken.uuid

            clients.append(client_data)

        # serialize clients as data for datatable
        context["clients_data"] = json.dumps(
            {"data": clients}, sort_keys=True, indent=1, cls=DjangoJSONEncoder
        )

        context["weights_label"] = weights_label

        return context

    def get(self, request, *args, **kwargs):
        """
        method only servers to run code for testing
        """
        return super().get(request, *args, **kwargs)


class AddCoach(LoginRequiredMixin, FormView):
    """docstring for AddCoach."""

    # Adds a coach-client object

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

        alreadyexists = (
            (CoachClient.objects.filter(coach=to_user, client=self.request.user))
            .distinct()
            .all()
        )

        # todo add any other validation we want to have for adding users as coaches

        if alreadyexists:
            messages.info(self.request, "Coach | Client relationship already exists")
            return super().form_invalid(form)

        else:
            CoachClient.objects.create(coach=to_user, client=self.request.user)

            # Creating a notification for the Coach
            action.send(
                self.request.user,
                verb=f"{self.request.user.username} has added you as a coach! You can view all your clients in the client tab.",
                target=to_user,
            )
            messages.info(self.request, "Added Coach")
            return super().form_valid(form)


class AddClient(LoginRequiredMixin, FormView):
    """docstring for AddClient."""

    # Adds a coach-client object

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

        alreadyexists = (
            (CoachClient.objects.filter(coach=self.request.user, client=to_user))
            .distinct()
            .all()
        )
        if alreadyexists:
            messages.info(self.request, "Coach | Client relationship already exists")
            return super().form_invalid(form)

        else:
            CoachClient.objects.create(coach=self.request.user, client=to_user)

            # Creating a notification for the Client
            action.send(
                self.request.user,
                verb=f"Coach {self.request.user.username} has added you as a client!",
                target=to_user,
            )
            messages.info(self.request, "Added Client")
            return super().form_valid(form)


class RemoveCoachClient(LoginRequiredMixin, FormView):
    """docstring for RemoveCoachClient."""

    # Removes an existing coach-client object

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

        # Lookup coach-client object in bidirectional way
        coachclient = (
            CoachClient.objects.filter(
                Q(coach=to_user, client=self.request.user)
                | Q(coach=self.request.user, client=to_user)
            )
            .distinct()
            .all()
        )

        if coachclient:
            coachclient.delete()

            messages.info(self.request, "Coach | Client Role Removed")
            return super().form_valid(form)

        else:
            messages.info(self.request, "Could not find Coach | Client Relationship")
            return super().form_invalid(form)
