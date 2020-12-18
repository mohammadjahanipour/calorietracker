from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import FormView, TemplateView
from friendship.models import Block, Follow, Friend, FriendshipRequest
from ..models import CoachClient
from django.db.models import Q
from django.contrib import messages
from actstream import action

from ..forms import (
    FriendForm,
    FriendShipRequestForm,
    LogDataForm,
    LoginForm,
    MeasurementWidget,
    RegisterForm,
    SettingForm,
)


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
        print("coaches", context["coaches"])

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
            messages.info(self.request, "Added Coach")
            return super().form_valid(form)


class AddClient(LoginRequiredMixin, FormView):
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
            (CoachClient.objects.filter(coach=self.request.user, client=to_user))
            .distinct()
            .all()
        )
        if alreadyexists:
            messages.info(self.request, "Coach | Client relationship already exists")
            return super().form_invalid(form)

        else:
            CoachClient.objects.create(coach=self.request.user, client=to_user)
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