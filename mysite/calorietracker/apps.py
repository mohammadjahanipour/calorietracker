from django.apps import AppConfig


class CalorietrackerConfig(AppConfig):
    name = 'calorietracker'

    def ready(self):
        import calorietracker.signals  # signal dependendcy

        # Actsream
        # from actstream import registry
        # registry.register(self.get_model('SomeModel'))
