from django.contrib.postgres.fields.array import ArrayField, ArrayContains
from django.contrib.postgres.fields.jsonb import JSONField
from django.db.models.lookups import BuiltinLookup, In, \
    Contains, StartsWith, EndsWith

class BaseAnyAllLookupMixin(object):
    def get_rhs_op(self, connection, rhs):
        if self.lookup_name == self.db_func:
            lookup_name = 'exact'
        else:
            lookup_name = self.lookup_name.split('%s_' % self.db_func)[1]
        operators = getattr(connection, '%s_operators' % self.db_func)
        return operators[lookup_name] % rhs

    def as_sql(self, compiler, connection):
        rhs_sql, rhs_params = self.process_lhs(compiler, connection)
        lhs_sql, params = self.process_rhs(compiler, connection)
        params.extend(rhs_params)
        rhs_sql = self.get_rhs_op(connection, rhs_sql)
        return '%s %s' % (lhs_sql, rhs_sql), params

class AnyLookupMixin(BaseAnyAllLookupMixin, BuiltinLookup):
    db_func = 'any'

class AllLookupMixin(BaseAnyAllLookupMixin, BuiltinLookup):
    db_func = 'all'

@ArrayField.register_lookup
class Any(AnyLookupMixin, BuiltinLookup):
    lookup_name = 'any'

@ArrayField.register_lookup
class AnyExact(AnyLookupMixin, BuiltinLookup):
    lookup_name = 'any_exact'

@ArrayField.register_lookup
class AnyGreaterThan(AnyLookupMixin, BuiltinLookup):
    lookup_name = 'any_gt'

@ArrayField.register_lookup
class AnyGreaterThanOrEqual(AnyLookupMixin, BuiltinLookup):
    lookup_name = 'any_gte'

@ArrayField.register_lookup
class AnyLessThan(AnyLookupMixin, BuiltinLookup):
    lookup_name = 'any_lt'

@ArrayField.register_lookup
class AnyLessThanOrEqual(AnyLookupMixin, BuiltinLookup):
    lookup_name = 'any_lte'

@ArrayField.register_lookup
class AnyLessThanOrEqual(AnyLookupMixin, Contains):
    lookup_name = 'any_in'

@ArrayField.register_lookup
class AnyStartOf(AnyLookupMixin, StartsWith):
    lookup_name = 'any_isstartof'

@ArrayField.register_lookup
class AnyEndOf(AnyLookupMixin, EndsWith):
    lookup_name = 'any_isendof'

@ArrayField.register_lookup
class All(AllLookupMixin):
    lookup_name = 'all'

@ArrayField.register_lookup
class AllExact(AllLookupMixin, BuiltinLookup):
    lookup_name = 'all_exact'

@ArrayField.register_lookup
class AllGreaterThan(AllLookupMixin, BuiltinLookup):
    lookup_name = 'all_gt'

@ArrayField.register_lookup
class AllGreaterThanOrEqual(AllLookupMixin, BuiltinLookup):
    lookup_name = 'all_gte'

@ArrayField.register_lookup
class AllLessThan(AllLookupMixin, BuiltinLookup):
    lookup_name = 'all_lt'

@ArrayField.register_lookup
class AllLessThanOrEqual(AllLookupMixin, BuiltinLookup):
    lookup_name = 'all_lte'

@ArrayField.register_lookup
class AllIn(AllLookupMixin, Contains):
    lookup_name = 'all_in'

@ArrayField.register_lookup
class AllStartOf(AllLookupMixin, StartsWith):
    lookup_name = 'all_isstartof'

@ArrayField.register_lookup
class AllEndOf(AnyLookupMixin, EndsWith):
    lookup_name = 'all_isendof'

@ArrayField.register_lookup
class AnyRegex(AnyLookupMixin, EndsWith):
    lookup_name = 'all_regex'

@ArrayField.register_lookup
class AnyContains(AnyLookupMixin, ArrayContains):
    lookup_name = 'any_contains'

class ContainsItem(ArrayContains):
    lookup_name = 'contains'
    def __init__(self, lhs, rhs):
        if not isinstance(rhs, (list, tuple)):
            rhs = [rhs]
        super(ContainsItem, self).__init__(lhs, rhs)