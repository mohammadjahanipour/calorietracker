"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from decorator_include import decorator_include
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage


from multifactor.decorators import multifactor_protected
import debug_toolbar

urlpatterns = [
    path('', decorator_include(multifactor_protected(factors=0), include("calorietracker.urls"))),
    path('admin/', decorator_include(multifactor_protected(factors=1), admin.site.urls)),
    path('multifactor/', include('multifactor.urls')),

    path("api/", include("api.urls")),
    re_path(
        r"^referrals/", include("pinax.referrals.urls", namespace="pinax_referrals")
    ),
    # re_path(r"^payments/", include("djstripe.urls", namespace="djstripe")), deprecated
    path("accounts/", include("allauth.urls")),
    path("friendship/", include("friendship.urls")),
    path('__debug__/', include(debug_toolbar.urls)),

    # Favicon redirect for legacy devices
    # This needs to be outside of any multifactor protected views and therefore cant be in the calorietracker app urls
    path(
        "favicon.ico/",
        RedirectView.as_view(url=staticfiles_storage.url("favicon/favicon.ico")),
    ),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
