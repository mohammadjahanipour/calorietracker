from django.urls import include
from django.urls import path
from . import views
from django.conf import settings

# app_name = "api"
# TODO: use namespace above
# TODO: check if tobar notification stuff did not break
# TODO: check if the friends page did not break 

urlpatterns = [


    path("ping/", views.Ping.as_view(), name="Ping"),

    path("usernames/<starts_with>/", views.UsernameList.as_view(), name="usernamelist"),
    path("usernames/", views.UsernameList.as_view(), name="usernamelist"),

    path("notification/<int:id>/clear/", views.ClearNotification.as_view(), name="clear_notification"),
    path("notifications/clear/", views.ClearAllNotification.as_view(), name="clear_all_notifications"),
]
