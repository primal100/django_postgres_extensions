from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.fields.related_lookups import RelatedExact, RelatedIn, RelatedGreaterThan, RelatedIsNull, \
    RelatedLessThan, RelatedGreaterThanOrEqual, RelatedLessThanOrEqual
from django.core import exceptions

class ArrayManyToManyRel(ForeignObjectRel):

    """
    Used by ManyToManyFields to store information about the relation.

    ``_meta.get_fields()`` returns this class to provide access to the field
    flags for the reverse relation.
    """
    def __init__(self, field, to, field_name, related_name=None, related_query_name=None,
                 limit_choices_to=None, symmetrical=True):
        super(ArrayManyToManyRel, self).__init__(
            field, to,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
        )

        self.model_name = to
        self.field_name = field_name
        self.symmetrical = symmetrical

    def get_join_on(self, parent_alias, lhs_col, table_alias, rhs_col):
        return '%s.%s = ANY(%s.%s)' % (
                parent_alias,
                lhs_col,
                table_alias,
                rhs_col,
            )

    def set_field_name(self):
        self.field_name = self.field_name or self.model._meta.pk.name

    def get_related_field(self):
        """
        Return the Field in the 'to' object to which this relationship is tied.
        """
        field = self.model._meta.get_field(self.field_name)
        if not field.concrete:
            raise exceptions.FieldDoesNotExist("No related field named '%s'" %
                    self.field_name)
        return field

    def get_lookup(self, lookup_name):
        if lookup_name == 'in':
            return RelatedIn
        elif lookup_name == 'exact':
            return RelatedExact
        elif lookup_name == 'gt':
            return RelatedGreaterThan
        elif lookup_name == 'gte':
            return RelatedGreaterThanOrEqual
        elif lookup_name == 'lt':
            return RelatedLessThan
        elif lookup_name == 'lte':
            return RelatedLessThanOrEqual
        elif lookup_name == 'isnull':
            return RelatedIsNull
        else:
            raise TypeError('Related Field got invalid lookup: %s' % lookup_name)