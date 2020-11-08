from django.db import models
from measurement import measures
from django.utils.deconstruct import deconstructible

# from safedelete.models import SafeDeleteModel
# from django.contrib.auth import get_user_model


class DateTimeFields(models.Model):
    """DatetimeFields"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


@deconstructible
class Weight(measures.Weight):
    pass


@deconstructible
class Distance(measures.Distance):
    pass