from django.db import models
# from safedelete.models import SafeDeleteModel
# from django.contrib.auth import get_user_model


class DateTimeFields(models.Model):
    """DatetimeFields"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
