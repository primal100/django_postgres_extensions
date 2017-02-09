from .widgets import NestedFormWidget
from django.forms.fields import MultiValueField, CharField
from django.core.exceptions import ValidationError


class NestedFormField(MultiValueField):
    """
    A Field that aggregates the logic of multiple Fields to create a nested form within a form.

    The compress method returns a dictionary of field names and values.

    Requires either a ``fields`` or ``keys`` argument but not both.

    The ``fields`` argument is a list of tuples; each tuple consisting of a field name and a field instance.
    If given a nested form will be created consisting of these fields.

    The ``keys`` argument is a list/tuple of field names. If given, a nested form will be created consisting of
    django.forms.CharField instances, with the given key names. This is primarily for use with
    django.contrib.postgres.HStoreField. By default, all fields are not required.

    To make all fields required set the ``require_all_fields`` argument to True.

    The ``max_value_length`` is ignored if the ``fields`` argument is given. If the ``keys`` argument is given, the max
    length for each CharField instance will be set to this value.

    Uses the NestedFormWidget.
    """
    def __init__(self, fields=(), keys=(), require_all_fields=False, max_value_length=25, *args, **kwargs):
        if (fields and keys) or (not fields and not keys):
            raise ValueError("NestedFormField requires either a tuple of fields or keys but not both")

        if keys:
            fields = []
            for key in keys:
                field = CharField(max_length=max_value_length, required=False)
                fields.append((key, field))
        form_fields = []
        widgets = []
        self.labels = []
        self.names = {}
        for field in fields:
            label = field[1].label or field[0]
            self.names[label] = field[0]
            self.labels.append(label)
            form_fields.append(field[1])
            widgets.append(field[1].widget)
        widget = NestedFormWidget(self.labels, widgets, self.names)
        super(NestedFormField, self).__init__(*args, fields=form_fields, widget=widget,
                                              require_all_fields=require_all_fields, **kwargs)

    def compress(self, data_list):
        result = {}
        for i, label in enumerate(self.labels):
            name = self.names[label]
            result[name] = data_list[i]
        return result

    def to_python(self, value):
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        else:
            raise ValidationError(
                self.error_messages['invalid_json'],
                code='invalid_json',
            )
