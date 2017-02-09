from django.db.models.expressions import Func, Expression
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE
from django.db.utils import six
from .expressions import F, Value as V

class SimpleFunc(Func):

    def __init__(self, field, *values, **extra):
        if not isinstance(field, Expression):
            field  = F(field)
            if values and not isinstance(values[0], Expression):
                values = [V(v) for v in values]
        super(SimpleFunc, self).__init__(field, *values, **extra)

class TooManyExpressionsError(Exception):
    pass

def multi_func(func, expression, *args):
    if len(args) > GET_ITERATOR_CHUNK_SIZE:
        raise TooManyExpressionsError('Multi-func given %s args. The limit is %s due to Python recursion depth risk' % (
        len(args), GET_ITERATOR_CHUNK_SIZE))
    args = list(args)
    initial_arg = args.pop(0)
    query = func(expression, initial_arg)
    for arg in args:
        query = func(query, arg)
    return query

def multi_array_remove(field, *args):
    return multi_func(ArrayRemove, field, *args)

class ArrayAppend(SimpleFunc):
    function = 'ARRAY_APPEND'

class ArrayPrepend(Func):
    function = 'ARRAY_PREPEND'

    def __init__(self, value, field, **extra):
        if not isinstance(value, Expression):
            value = V(value)
            field = F(field)
        super(ArrayPrepend, self).__init__(value, field, **extra)

class ArrayRemove(SimpleFunc):
    function = 'ARRAY_REMOVE'

class ArrayReplace(SimpleFunc):
    function = 'ARRAY_REPLACE'

class ArrayPosition(SimpleFunc):
    function = 'ARRAY_POSITION'

class ArrayPositions(SimpleFunc):
    function = 'ARRAY_POSITIONS'

class ArrayCat(Func):
    function = 'ARRAY_CAT'

    def __init__(self, field, value, prepend=False, output_field=None, **extra):
        if not isinstance(field, Expression):
            field = F(field)
        if not isinstance(value, Expression):
            if isinstance(value, six.string_types):
                value = F(value)
            elif output_field:
                value = V(value, output_field = output_field)
            else:
                value = V(value)
        if prepend:
            super(ArrayCat, self).__init__(value, field, **extra)
        else:
            super(ArrayCat, self).__init__(field, value, **extra)

class ArrayLength(SimpleFunc):
    function = 'ARRAY_LENGTH'

class ArrayDims(SimpleFunc):
    function = 'ARRAY_DIMS'

class ArrayUpper(SimpleFunc):
    function = 'ARRAY_UPPER'

class ArrayLower(SimpleFunc):
    function = 'ARRAY_LOWER'

class Cardinality(SimpleFunc):
    function = 'CARDINALITY'

class NonFieldFunc(Func):
    def __init__(self, *values, **extra):
        values = list(values)
        for i, value in enumerate(values):
            if not isinstance(value, Expression):
                values[i] = V(value)
        super(NonFieldFunc, self).__init__(*values, **extra)

class HStore(NonFieldFunc):
    function = 'HSTORE'

class AKeys(SimpleFunc):
    function = 'AKEYS'

class SKeys(SimpleFunc):
    function = 'SKEYS'

class AVals(SimpleFunc):
    function = 'AVALS'

class SVals(SimpleFunc):
    function = 'SVALS'

class HStoreToArray(SimpleFunc):
    function = 'HSTORE_TO_ARRAY'

class HStoreToMatrix(SimpleFunc):
    function = 'HSTORE_TO_MATRIX'

class Slice(SimpleFunc):
    function = 'SLICE'

class Delete(SimpleFunc):
    function = 'DELETE'

class Each(SimpleFunc):
    function = 'EACH'

class HstoreToJSONB(SimpleFunc):
    function = 'HSTORE_TO_JSONB'

class HstoreToJSONBLoose(SimpleFunc):
    function = 'HSTORE_TO_JSONB_LOOSE'

class ToJSONB(NonFieldFunc):
    function = 'TO_JSONB'

class RowToJSON(SimpleFunc):
    function = 'ROW_TO_JSON'

class ArrayToJSON(SimpleFunc):
    function = 'ARRAY_TO_JSON'

class JSONBBuildArray(NonFieldFunc):
    function = 'JSONB_BUILD_ARRAY'

class JSONBArrayElements(SimpleFunc):
    function = 'JSONB_ARRAY_ELEMENTS'

class JSONBBuildObject(NonFieldFunc):
    function = 'JSONB_BUILD_OBJECT'

class JSONBObject(NonFieldFunc):
    function = 'JOSNB_OBJECT'

class JSONBSet(SimpleFunc):
    function = 'JSONB_SET'

class JSONBArrayLength(SimpleFunc):
    function = 'JSONB_ARRAY_length'

class JSONBPretty(SimpleFunc):
    function = 'JSONB_PRETTY'

class JSONObjectKeys(SimpleFunc):
    function = 'JSON_OBJECT_KEYS'

class JSONStripNulls(SimpleFunc):
    function = 'JSON_STRIP_NULLS'

class JSONTypeOf(SimpleFunc):
    function = 'JSON_TYPE_OF'