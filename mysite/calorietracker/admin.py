from django.contrib import admin

from .models import Setting, Log

admin.site.site_header = 'CalorieTracker'
admin.site.site_title = 'CalorieTracker'

admin.site.register(Setting)
admin.site.register(Log)
