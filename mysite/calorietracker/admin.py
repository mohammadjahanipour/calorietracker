from django.contrib import admin

from .models import Setting, Log, Feedback, Streak, Subscription, MFPCredentials, Wallet

admin.site.site_header = "CalorieTracker"
admin.site.site_title = "CalorieTracker"

admin.site.register(Setting)
admin.site.register(Log)
admin.site.register(Feedback)
admin.site.register(Streak)
admin.site.register(Subscription)
admin.site.register(MFPCredentials)
admin.site.register(Wallet)