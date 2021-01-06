from django.db.backends.sqlite3 import base, features


class DatabaseFeatures(features.DatabaseFeatures):
    """
    """


class DatabaseWrapper(base.DatabaseWrapper):
    features_class = DatabaseFeatures
