from django.db import models
from django_postgres_extensions.models.fields.related import ArrayManyToManyField

class NumberTraditional(models.Model):
    index = models.IntegerField()

    def __str__(self):
        return self.index

class Traditional(models.Model):
    index = models.IntegerField()
    numbers = models.ManyToManyField(NumberTraditional)

def __str__(self):
    return self.index

class NumberArray(models.Model):
    index = models.IntegerField()

    def __str__(self):
        return self.index

class Array(models.Model):
    index = models.IntegerField()
    numbers = ArrayManyToManyField(NumberArray, db_index=False)

    def __str__(self):
        return self.index