from django.urls import include
from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [


    path("ping/", views.Ping.as_view(), name="Ping"),

    path("usernames/<starts_with>/", views.UsernameList.as_view(), name="usernamelist"),
    path("usernames/", views.UsernameList.as_view(), name="usernamelist"),
]
