from django.contrib import admin

from .models import Setting, Log

admin.site.register(Setting)
admin.site.register(Log)
