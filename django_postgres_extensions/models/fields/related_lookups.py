from django.db.models.fields.related_lookups import RelatedLookupMixin, MultiColSource, get_normalized_value
from django.contrib.postgres.fields.array import ArrayContains, ArrayContainedBy, ArrayExact, ArrayOverlap

from django_postgres_extensions.models.lookups import (
    AnyExact, AnyGreaterThan, AnyLessThan, AnyGreaterThanOrEqual, AnyLessThanOrEqual, ContainsItem)

class RelatedArrayMixin(RelatedLookupMixin):
    def get_prep_lookup(self):
        self.lookup_name = 'contains'
        if not isinstance(self.lhs, MultiColSource) and self.rhs_is_direct_value():
            self.rhs = [get_normalized_value(value, self.lhs)[0] for value in self.rhs]
            if hasattr(self.lhs.output_field, 'get_path_info'):
                self.rhs = [self.lhs.output_field.get_path_info()[-1].target_fields[-1].get_prep_value(rhs) for rhs in
                            self.rhs]
        self.lookup_name = 'exact'
        return super(RelatedLookupMixin, self).get_prep_lookup()

class RelatedAnyExact(RelatedLookupMixin, AnyExact):
    pass

class RelatedAnyGreaterThan(RelatedLookupMixin, AnyGreaterThan):
    pass

class RelatedAnyLessThan(RelatedLookupMixin, AnyLessThan):
    pass

class RelatedAnyGreaterThanOrEqual(RelatedLookupMixin, AnyGreaterThanOrEqual):
    pass

class RelatedAnyLessThanOrEqual(RelatedLookupMixin, AnyLessThanOrEqual):
    pass

class RelatedArrayExact(RelatedArrayMixin, ArrayExact):
    """
    More like what exact should be. Checks the array contains the array of related objects and only those related objects
    """
    pass

class RelatedArrayContains(RelatedArrayMixin, ArrayContains):
    pass

class RelatedContainsItem(RelatedArrayMixin, ContainsItem):
    pass

class RelatedArrayContainedBy(RelatedArrayMixin, ArrayContainedBy):
    pass

class RelatedArrayOverlap(RelatedArrayMixin, ArrayOverlap):
    pass