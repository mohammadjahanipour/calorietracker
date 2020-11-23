from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from . serializer import UsernameSerializer
from django.contrib.auth import get_user_model
from rest_framework import authentication, permissions
from actstream.models import target_stream




class Ping(APIView):
    """Returns Pong if successful """

    def get(self, request):
        return Response({'ping': "pong"})


class Endpoints(object):
    """Returns the available endpoints"""
    # TODO: is there no method to get all the routes dynamically?

    def get(self, request):
        return Response({'ping': "pong"})


class UsernameList(generics.ListAPIView):

    """
    Returns a list of all usernames
    if starts_with is given usernames that start with the given value

    starts_with is given as url parameter
    standard limitations of this apply but no further limitations have been imposed
    """

    queryset = get_user_model().objects.all()
    serializer_class = UsernameSerializer

    def get_queryset(self, *args, **kwargs):

        starts_with = self.kwargs.get("starts_with", False)

        if starts_with:
            return get_user_model().objects.filter(username__startswith=starts_with)

        else:
            return get_user_model().objects.all()


class ClearNotification(APIView):
    """Removes the user as the target for a given actstream action"""


    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]


    def patch(self, request, id, *args, **kwargs):

        notifications = request.user.target_actions.filter(id=id)

        for notification in notifications:

            notification.target = None
            notification.save()

        return Response({})


class ClearAllNotification(APIView):
    """
    Removes the user from all actstream actions where he is the target
    effectivly clearing notifications for the user
    """


    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]


    def patch(self, request ,*args, **kwargs):

        notifications = target_stream(request.user)

        for notification in notifications:
            # This might be slow on large queries but provides safety and should be fine
            notification.target = None
            notification.save()

        return Response({})
