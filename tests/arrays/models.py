from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import HStoreField
from django_postgres_extensions.models.fields.related import ArrayField

class Product(models.Model):
    name = models.CharField(max_length=3)
    tags = ArrayField(models.CharField(max_length=15), null=True, blank=True)
    moretags = ArrayField(models.CharField(max_length=15), null=True, blank=True)
    prices = ArrayField(models.IntegerField(), null=True, blank=True)
    description = HStoreField(null=True, blank=True)
    coordinates = ArrayField(ArrayField(models.IntegerField()), null=True)