Querysets
=========

Additional Queryset Methods
---------------------------
This app adds the format method to all querysets. This will defer a field and add an annotation with a different format.
For example to return a hstorefield as json::

    qs = Model.objects.all().format('description', HstoreToJSONBLoose)
