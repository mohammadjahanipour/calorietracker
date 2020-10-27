from django.contrib import admin
from django.apps import apps

admin.site.site_header = "CalorieTracker"
admin.site.site_title = "CalorieTracker"

myapp = apps.get_app_config("calorietracker")
for model in myapp.get_models():
    admin.site.register(model)
