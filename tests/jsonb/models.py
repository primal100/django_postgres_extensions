from django.db import models
from django_postgres_extensions.models.fields import JSONField

class Product(models.Model):
    name = models.CharField(max_length=3)
    description = JSONField(null=True, blank=True)