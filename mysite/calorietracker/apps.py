from django.apps import AppConfig
from django.contrib.auth import get_user_model




class CalorietrackerConfig(AppConfig):
    name = 'calorietracker'

    def ready(self):
        import calorietracker.signals  # signal dependendcy



        # Actsream
        from actstream import registry

        # registry.register(self.get_model('User'))

        # User Model registration
        # assumes default django user model
        # needs adjustment if custom user model is used
        # also not 100% sure if this is the correct way to handle this but no docs on it afaik

        from django.contrib.auth.models import User
        registry.register(User)
