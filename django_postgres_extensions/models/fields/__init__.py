from django.contrib.postgres import fields
from django.contrib.postgres.forms import SplitArrayField as SplitArrayFormField
from django.forms.fields import TypedMultipleChoiceField
from psycopg2.extras import Json
from django_postgres_extensions.forms.fields import NestedFormField
from django_postgres_extensions.models.expressions import F, Value as V
from django_postgres_extensions.models.functions import HStore, Delete, ArrayRemove
from django_postgres_extensions.models.sql.updates import UpdateArrayByIndex
from django.core import exceptions


class ArrayField(fields.ArrayField):

    def __init__(self, base_field, form_size=None, **kwargs):
        super(ArrayField, self).__init__(base_field, **kwargs)
        self.form_size = form_size

    def get_update_type(self, indexes, value):
        if indexes == 'del':
            return ArrayRemove(self.name, value)
        if '__' in indexes:
            indexes = indexes.split('__')
        try:
            indexes = [int(index) + 1 for index in indexes]
            return UpdateArrayByIndex(indexes, value, self)
        except ValueError:
            raise ValueError('Update lookup type %s not found for field %s' % (indexes, self.name))

    def formfield(self, **kwargs):
        if self.form_size or self.choices:
            defaults = {
                'form_class': SplitArrayFormField,
                'base_field': self.base_field.formfield(),
                'choices_form_class': TypedMultipleChoiceField,
                'size': self.form_size,
                'remove_trailing_nulls': True
            }
            if self.choices:
                defaults['coerce'] = self.base_field.to_python
            defaults.update(kwargs)
            return super(fields.ArrayField, self).formfield(**defaults)
        return super(ArrayField, self).formfield(**kwargs)

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. Subclasses should override
        this to provide validation logic.
        """
        if not self.editable:
            # Skip validation for non-editable fields.
            return

        if self.choices and value not in self.empty_values:
            if isinstance(value, (list, tuple)):
                option_keys = [x[0] for x in self.choices]
                if all(x in option_keys for x in value):
                    return
            else:
                for option_key, option_value in self.choices:
                    if isinstance(option_value, (list, tuple)):
                        # This is an optgroup, so look inside the group for
                        # options.
                        for optgroup_key, optgroup_value in option_value:
                            if value == optgroup_key:
                                return
                    elif value == option_key:
                        return
            raise exceptions.ValidationError(
                self.error_messages['invalid_choice'],
                code='invalid_choice',
                params={'value': value},
            )

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'], code='null')

        if not self.blank and value in self.empty_values:
            raise exceptions.ValidationError(self.error_messages['blank'], code='blank')

    def deconstruct(self):
        name, path, args, kwargs = super(ArrayField, self).deconstruct()
        kwargs.update({
            'form_size': self.form_size,
        })
        return name, path, args, kwargs

class HStoreField(fields.HStoreField):

    def __init__(self, fields=(), keys=(), max_value_length=25, require_all_fields=False, **kwargs):
        super(HStoreField, self).__init__(**kwargs)
        self.fields = fields
        self.keys = keys
        self.max_value_length = max_value_length
        self.require_all_fields = require_all_fields

    def get_update_type(self, lookups, value):
        lookup = lookups[0]
        if lookup == '' or lookup == 'raw':
            keys = list(value.keys())
            values = list(value.values())
            if lookup == '':
                values = [str(v) for v in value.values()]
            return F(self.name).cat(HStore(V(keys), V(values)))
        if lookup == 'del':
            return Delete(self.name, value)
        raise ValueError('Update lookup type %s not found for field %s' % (lookup, self.name))

    def formfield(self, **kwargs):
        if self.fields or self.keys:
            defaults = {
                'form_class': NestedFormField,
                'fields': self.fields,
                'keys': list(self.keys),
                'require_all_fields': self.require_all_fields,
                'max_value_length': self.max_value_length
            }
            defaults.update(kwargs)
        else:
            defaults = kwargs
        return super(HStoreField, self).formfield(**defaults)

class JSONField(fields.JSONField):

    def __init__(self, fields=(), require_all_fields=False, **kwargs):
        super(JSONField, self).__init__(**kwargs)
        self.fields = fields
        self.require_all_fields = require_all_fields

    def get_update_type(self, lookups, value):
        lookup = lookups[0]
        if lookup == '':
            return F(self.name).cat(V(Json(value)))
        if lookup == 'del':
            if '__' in value:
                values = value.split('__')
                return F(self.name).delete(V(values))
            return F(self.name) - V(value)
        raise ValueError('Update lookup type %s not found for field %s' % (lookup, self.name))

    def formfield(self, **kwargs):
        if self.fields:
            defaults = {
                'form_class': NestedFormField,
                'fields': self.fields,
                'require_all_fields': self.require_all_fields,
            }
            defaults.update(kwargs)
        else:
            defaults = kwargs
        return super(JSONField, self).formfield(**defaults)
