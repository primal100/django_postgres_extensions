from django.db.models.expressions import F as BaseF, Value as BaseValue, Func, Expression
from django.db.utils import six
from django.contrib.postgres.fields.array import IndexTransform
from django.utils.functional import cached_property
from django.db.models.lookups import Transform

class OperatorMixin(object):
    CAT = '||'
    REPLACE = '#='
    DELETE = '#-'
    KEY = '->'
    KEYTEXT = '->>'
    PATH = '#>'
    PATHTEXT = '#>>'

    def cat(self, other):
        return self._combine(other, self.CAT, False)

    def replace(self, other):
        return self._combine(other, self.REPLACE, False)

    def delete(self, other):
        return self._combine(other, self.DELETE, False)

    def key(self, other):
        return self._combine(other, self.KEY, False)

    def keytext(self, other):
        return self._combine(other, self.KEYTEXT, False)

    def path(self, other):
        return self._combine(other, self.PATH, False)

    def pathtext(self, other):
        return self._combine(other, self.PATHTEXT, False)

class F(BaseF, OperatorMixin):
    pass

class Value(BaseValue, OperatorMixin):
    def as_sql(self, compiler, connection):
        if self._output_field and any(self._output_field.get_internal_type() == fieldname for fieldname in
                                      ['ArrayField', 'MultiReferenceArrayField']):
            base_field = self._output_field.base_field
            return '%s::%s[]' % ('%s', base_field.db_type(connection)), [self.value]
        return super(Value, self).as_sql(compiler, connection)

class Index(IndexTransform):
    def __init__(self, field, index, *args, **kwargs):
        if not isinstance(field, Expression):
            field = F(field)
        super(Index, self).__init__(index + 1, None, field, *args, **kwargs)

    @cached_property
    def default_alias(self):
        return '%s__%s' % (self.lhs.name, self.index - 1)

    @property
    def name(self):
        return self.default_alias

    @property
    def output_field(self):
        return self.lhs.field.base_field

class SliceArray(Transform):
    def __init__(self, field, *indexes, **kwargs):
        if isinstance(field, SliceArray):
            self.multidimensional = True
        else:
            field = F(field)
            self.multidimensional = False
        self.indexes = [i + 1 for i in indexes]
        super(SliceArray, self).__init__(field, **kwargs)

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return '%s[%s:%s]' % (lhs, self.indexes[0], self.indexes[1]), params

    @cached_property
    def default_alias(self):
        return '%s__%s_%s' % (self.lhs.name, self.indexes[0] - 1, self.indexes[1] - 1)

    @property
    def name(self):
        return self.default_alias

    @property
    def output_field(self):
        if self.multidimensional:
            return self.lhs.field
        return self.lhs.field.base_field


def Key(field, keys_string):
    if isinstance(keys_string, six.string_types) and '__' in keys_string:
        keys = keys_string.split('__')
        expression = F(field).path(Value(keys))
    else:
        expression = F(field).key(Value(keys_string))
    expression.default_alias = "%s__%s" % (field, keys_string)
    return expression

def Keys(field, keys):
    expression = F(field).key(Value(keys))
    expression.default_alias = "%s__selected" % field
    return expression
