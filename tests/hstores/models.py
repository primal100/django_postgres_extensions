from __future__ import unicode_literals

from django.db import models
from django_postgres_extensions.models.fields import ArrayField, HStoreField

class Product(models.Model):
    name = models.CharField(max_length=3)
    description = HStoreField(null=True, blank=True)
    details = HStoreField(null=True, blank=True)
    purchases = ArrayField(HStoreField(), null=True)