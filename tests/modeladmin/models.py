from django.db import models
from django_postgres_extensions.models.fields import HStoreField, JSONField, ArrayField
from django_postgres_extensions.models.fields.related import ArrayManyToManyField
from django import forms
from django.contrib.postgres.forms import SplitArrayField
from django_postgres_extensions.forms.fields import NestedFormField

details_fields = (
    ('Brand', NestedFormField(keys=('Name', 'Country'))),
     ('Type', forms.CharField(max_length=25, required=False)),
     ('Colours', SplitArrayField(base_field=forms.CharField(max_length=10, required=False), size=10)),
)

class Buyer(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=15)
    keywords = ArrayField(models.CharField(max_length=20), default=[], form_size=10, blank=True)
    sports = ArrayField(models.CharField(max_length=20),default=[], blank=True, choices=(
    ('football', 'Football'), ('tennis', 'Tennis'), ('golf', 'Golf'), ('basketball', 'Basketball'), ('hurling', 'Hurling'), ('baseball', 'Baseball')))
    shipping = HStoreField(keys=('Address', 'City', 'Region', 'Country'), blank=True, default={})
    details = JSONField(fields=details_fields, blank=True, default={})
    buyers =  ArrayManyToManyField(Buyer)

    def __str__(self):
        return self.name

    @property
    def country(self):
        return self.shipping.get('Country', '')
