from django_postgres_extensions.models.fields import ArrayField
from django.db.models.fields.related import RelatedField
from django.db.models.query_utils import PathInfo
from .reverse_related import ArrayManyToManyRel
from .related_descriptors import MultiReferenceDescriptor
from django.db import models
from django.db.models.fields.related import RECURSIVE_RELATIONSHIP_CONSTANT, lazy_related_operation
from django.forms.models import ModelMultipleChoiceField
from django.utils import six
from django.utils.encoding import force_text
from .related_lookups import RelatedArrayContains, RelatedArrayExact, RelatedArrayContainedBy, RelatedContainsItem, \
    RelatedArrayOverlap, RelatedAnyGreaterThan, RelatedAnyLessThanOrEqual, RelatedAnyLessThan, RelatedAnyGreaterThanOrEqual

class ArrayManyToManyField(ArrayField, RelatedField):
    # Field flags
    many_to_many_array = True
    many_to_many = False
    many_to_one = False
    one_to_many = False
    one_to_one = False

    rel_class = ArrayManyToManyRel

    def __init__(self, to_model, base_field=None, size=None, related_name=None, symmetrical=None,
                 related_query_name=None, limit_choices_to=None, to_field=None, db_constraint=False, **kwargs):

        try:
            to = to_model._meta.model_name
        except AttributeError:
            assert isinstance(to_model, six.string_types), (
                "%s(%r) is invalid. First parameter to ForeignKey must be "
                "either a model, a model name, or the string %r" % (
                    self.__class__.__name__, to_model,
                    RECURSIVE_RELATIONSHIP_CONSTANT,
                )
            )
            to = str(to_model)
        else:
            # For backwards compatibility purposes, we need to *try* and set
            # the to_field during FK construction. It won't be guaranteed to
            # be correct until contribute_to_class is called. Refs #12190.
            to_field = to_field or (to_model._meta.pk and to_model._meta.pk.name)
            if not base_field:
                field = to_model._meta.get_field(to_field)
                if not field.is_relation:
                    base_field_type = type(field)
                    internal_type = field.get_internal_type()
                    if internal_type == 'AutoField':
                        pass
                    elif internal_type == 'BigAutoField':
                        base_field = models.BigIntegerField()
                    elif hasattr(field, 'max_length'):
                        base_field = base_field_type(max_length = field.max_length)
                    else:
                        base_field = base_field_type()

        if not base_field:
            base_field = models.IntegerField()

        if symmetrical is None:
            symmetrical = (to == RECURSIVE_RELATIONSHIP_CONSTANT)

        kwargs['rel'] = self.rel_class(
            self, to, to_field,
            related_name=related_name,
            related_query_name=related_query_name,
            limit_choices_to=limit_choices_to,
            symmetrical=symmetrical,
        )
        self.has_null_arg = 'null' in kwargs

        self.db_constraint = db_constraint

        self.to = to

        if 'default' not in kwargs.keys():
            kwargs['default'] = []
        kwargs['blank'] = True

        self.from_fields = ['self']
        self.to_fields = [to_field]

        super(ArrayManyToManyField, self).__init__(base_field, size=size, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ArrayManyToManyField, self).deconstruct()
        args = (self.to,)
        kwargs.update({
            'base_field': self.base_field,
            'size': self.size,
            'related_name': self.remote_field.related_name,
            'symmetrical': self.remote_field.symmetrical,
            'related_query_name': self.remote_field.related_query_name,
            'limit_choices_to': self.remote_field.limit_choices_to,
            'to_field': self.remote_field.field,
            'db_constraint': self.db_constraint
        })
        return name, path, args, kwargs

    def get_attname(self):
        return '%s_ids' % self.name

    def get_attname_column(self):
        attname = self.get_attname()
        column = self.db_column or attname
        return attname, column

    def get_accessor_name(self):
        return self.remote_field.model_name  + '_set'

    def get_reverse_accessor_name(self):
        return self.remote_field.get_accessor_name()

    def contribute_to_class(self, cls, name, **kwargs):
        # To support multiple relations to self, it's useful to have a non-None
        # related name on symmetrical relations for internal reasons. The
        # concept doesn't make a lot of sense externally ("you want me to
        # specify *what* on my non-reversible relation?!"), so we set it up
        # automatically. The funky name reduces the chance of an accidental
        # clash.
        if self.remote_field.symmetrical and (
                self.remote_field.model == "self" or self.remote_field.model == cls._meta.object_name):
            self.remote_field.related_name = "%s_rel_+" % name
        elif self.remote_field.is_hidden():
            # If the backwards relation is disabled, replace the original
            # related_name with one generated from the m2m field name. Django
            # still uses backwards relations internally and we need to avoid
            # clashes between multiple m2m fields with related_name == '+'.
            self.remote_field.related_name = "_%s_%s_+" % (cls.__name__.lower(), name)

        super(ArrayManyToManyField, self).contribute_to_class(cls, name)

        if not cls._meta.abstract:
            setattr(cls, self.name, MultiReferenceDescriptor(self.remote_field, reverse=False))

            self.opts = cls._meta
            if self.remote_field.related_name:
                related_name = force_text(self.remote_field.related_name) % {
                    'class': cls.__name__.lower(),
                    'app_label': cls._meta.app_label.lower()
                }
                self.remote_field.related_name = related_name

            def resolve_related_class(model, related, field):
                field.remote_field.model = related
                field.do_related_class(related, model)

            lazy_related_operation(resolve_related_class, cls, self.remote_field.model, field=self)

    def contribute_to_related_class(self, cls, related):
        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not self.remote_field.is_hidden() and not related.related_model._meta.swapped:
            setattr(cls, self.get_reverse_accessor_name(), MultiReferenceDescriptor(self.remote_field, reverse=True))

    def formfield(self, **kwargs):
        db = kwargs.pop('using', None)
        defaults = {
            'form_class': ModelMultipleChoiceField,
            'queryset': self.related_model._default_manager.using(db),
        }
        defaults.update(kwargs)
        # If initial is passed in, it's a list of related objects, but the
        # MultipleChoiceField takes a list of IDs.
        if defaults.get('initial') is not None:
            initial = defaults['initial']
            if callable(initial):
                initial = initial()
            defaults['initial'] = [i._get_pk_val() for i in initial]
        return super(RelatedField, self).formfield(**defaults)

    def get_join_on(self, parent_alias, lhs_col, table_alias, rhs_col):
        return '%s.%s = ANY(%s.%s)' % (
                table_alias,
                rhs_col,
                parent_alias,
                lhs_col,
            )

    def get_join_on2(self, parent_alias, lhs_col, table_alias, rhs_col):
        return "ARRAY_APPEND(ARRAY[]::integer[], %s.%s) <@ ANY(%s.%s)" % (
                table_alias,
                rhs_col,
                parent_alias,
                lhs_col,
            )

    def resolve_related_fields(self):
        if len(self.from_fields) < 1 or len(self.from_fields) != len(self.to_fields):
            raise ValueError('Foreign Object from and to fields must be the same non-zero length')
        if isinstance(self.remote_field.model, six.string_types):
            raise ValueError('Related model %r cannot be resolved' % self.remote_field.model)
        related_fields = []
        for index in range(len(self.from_fields)):
            from_field_name = self.from_fields[index]
            to_field_name = self.to_fields[index]
            from_field = (self if from_field_name == 'self'
                          else self.opts.get_field(from_field_name))
            to_field = (self.remote_field.model._meta.pk if to_field_name is None
                        else self.remote_field.model._meta.get_field(to_field_name))
            related_fields.append((from_field, to_field))
        return related_fields


    @property
    def related_fields(self):
        if not hasattr(self, '_related_fields'):
            self._related_fields = self.resolve_related_fields()
        return self._related_fields


    @property
    def reverse_related_fields(self):
        return [(rhs_field, lhs_field) for lhs_field, rhs_field in self.related_fields]


    @property
    def local_related_fields(self):
        return tuple(lhs_field for lhs_field, rhs_field in self.related_fields)


    @property
    def foreign_related_fields(self):
        return tuple(rhs_field for lhs_field, rhs_field in self.related_fields if rhs_field)


    def get_local_related_value(self, instance):
        return self.get_instance_value_for_fields(instance, self.local_related_fields)


    def get_foreign_related_value(self, instance):
        return self.get_instance_value_for_fields(instance, self.foreign_related_fields)


    @staticmethod
    def get_instance_value_for_fields(instance, fields):
        ret = []
        opts = instance._meta
        for field in fields:
            # Gotcha: in some cases (like fixture loading) a model can have
            # different values in parent_ptr_id and parent's id. So, use
            # instance.pk (that is, parent_ptr_id) when asked for instance.id.
            if field.primary_key:
                possible_parent_link = opts.get_ancestor_link(field.model)
                if (not possible_parent_link or
                        possible_parent_link.primary_key or
                        possible_parent_link.model._meta.abstract):
                    ret.append(instance.pk)
                    continue
            ret.append(getattr(instance, field.attname))
        return tuple(ret)

    def get_joining_columns(self, reverse_join=False):
        source = self.reverse_related_fields if reverse_join else self.related_fields
        columns = tuple((lhs_field.column, rhs_field.column) for lhs_field, rhs_field in source)
        return columns

    def get_reverse_joining_columns(self):
        return self.get_joining_columns(reverse_join=True)

    def get_extra_descriptor_filter(self, instance):
        """
        Return an extra filter condition for related object fetching when
        user does 'instance.column', that is the extra filter is used in
        the descriptor of the field.

        The filter should be either a dict usable in .filter(**kwargs) call or
        a Q-object. The condition will be ANDed together with the relation's
        joining columns.

        A parallel method is get_extra_restriction() which is used in
        JOIN and subquery conditions.
        """
        return {}

    def get_extra_restriction(self, where_class, alias, related_alias):
        """
        Return a pair condition used for joining and subquery pushdown. The
        condition is something that responds to as_sql(compiler, connection)
        method.

        Note that currently referring both the 'alias' and 'related_alias'
        will not work in some conditions, like subquery pushdown.

        A parallel method is get_extra_descriptor_filter() which is used in
        instance.column related object fetching.
        """
        return None

    def get_path_info(self, filtered_relation=None):
        """
        Get path from this field to the related model.
        """
        opts = self.remote_field.model._meta
        from_opts = self.model._meta
        return [PathInfo(from_opts, opts, self.foreign_related_fields, self, False, True, filtered_relation)]

    def validate_item(self, obj, model=None):
        if not model:
            model = self.remote_field.model
        if isinstance(obj, model):
            obj = getattr(obj, self.remote_field.target_field.name)
        elif isinstance(obj, models.Model):
            raise TypeError(
                "'%s' instance expected, got %r" %
                (model._meta.object_name, obj)
            )
        return obj

    def save_form_data(self, instance, data):
        """
        For newly created instances, the column is set and saved with all the
        other fields when model.save() is run. So m2m can be updated along with
        all the other fields with one sql query.
        For updateing instances with model.save(), Array M2M fields are ignored to avoid sending large
        amounts of unneccessary data in the update query. Instead the data is set with an
        extra sql command via the descriptor.
        """
        if instance.pk:
            getattr(instance, self.name).set(data)
        else:
            objs = [self.validate_item(obj) for obj in data]
            setattr(instance, self.attname, objs)

    def get_reverse_path_info(self, filtered_relation):
        """
        Get path from the related model to this field's model.
        """
        opts = self.model._meta
        from_opts = self.remote_field.model._meta
        pathinfos = [PathInfo(from_opts, opts, (from_opts.pk,), self.remote_field, not self.unique, False, filtered_relation)]
        return pathinfos

    def get_lookup(self, lookup_name):
        if lookup_name == 'in':
            return RelatedArrayOverlap
        elif lookup_name == 'exact':
            return RelatedContainsItem
        elif lookup_name =='exactly':
            return RelatedArrayExact
        elif lookup_name == 'contains':
            return RelatedArrayContains
        elif lookup_name == 'contained_by':
            return RelatedArrayContainedBy
        elif lookup_name == 'overlap':
            return RelatedArrayOverlap
        elif lookup_name == 'gt':
            return RelatedAnyGreaterThan
        elif lookup_name == 'gte':
            return RelatedAnyGreaterThanOrEqual
        elif lookup_name == 'lt':
            return RelatedAnyLessThan
        elif lookup_name == 'lte':
            return RelatedAnyLessThanOrEqual
        else:
            raise TypeError('Related Array got invalid lookup: %s' % lookup_name)