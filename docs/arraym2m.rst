Array Many To Many Field
========================

Basic Usage
-----------

The Array Many To Many Field is designed be a drop-in replacement for the normal Django Many To Many Field
except that it uses an array instead of a separate table to store relationships, but replicates many of the same features.
In general, write queries are much faster than the traditional M2M however select queries are typically slower.

To use this field, it is required to set ENABLE_ARRAY_M2M = True in settings.py (to enable the required monkey-patching)::

    ENABLE_ARRAY_M2M = True

Then in models.py::

    from django.db import models
    from django_postgres_extensions.models.fields import ArrayManyToManyField

    class Publication(models.Model):
        title = models.CharField(max_length=30)

        def __str__(self):
            return self.title

        class Meta:
            ordering = ('title',)

    class Article(models.Model):
        headline = models.CharField(max_length=100)
        publications = ArrayManyToManyField(Publication, name='publications')

        def __str__(self):
            return self.headline

        class Meta:
            ordering = ('headline',)

The Array Many To Many field supports the following features which replicate the API of the regular Many To Many Field:

- Descriptor queryset with add, remove, clear and set for both forward and reverse relationships
- Prefetch related for both forward and reverse relationships
- Lookups across relationships with filter for both forward and reverse relationships
- Lookups across relationships with exclude for for forward relationships only

You can find more information on how these features work in the Django documentation for the regular Many To Many Field:

https://docs.djangoproject.com/en/1.9/topics/db/examples/many_to_many/
