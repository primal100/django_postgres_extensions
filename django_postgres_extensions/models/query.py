from django.db import transaction
from django.core import exceptions
from django.db.models.sql.constants import CURSOR
from .sql import UpdateQuery
import copy



def update(self, **kwargs):
    """
    Updates all elements in the current QuerySet, setting all the given
    fields to the appropriate values.
    """
    assert self.query.can_filter(), \
        "Cannot update a query once a slice has been taken."
    self._for_write = True
    query = self.query.clone(UpdateQuery)
    query.add_update_values(kwargs)
    with transaction.atomic(using=self.db, savepoint=False):
        rows = query.get_compiler(self.db).execute_sql(CURSOR)
    self._result_cache = None
    return rows
update.alters_data = True


def _update(self, values):
    """
    A version of update that accepts field objects instead of field names.
    Used primarily for model saving and not intended for use by general
    code (it requires too much poking around at model internals to be
    useful at that level).
    """
    assert self.query.can_filter(), \
        "Cannot update a query once a slice has been taken."
    query = self.query.clone(UpdateQuery)
    values = [value for value in values if not getattr(value[0], 'many_to_many_array', False)]
    query.add_update_fields(values)
    self._result_cache = None
    return query.get_compiler(self.db).execute_sql(CURSOR)
_update.alters_data = True
_update.queryset_only = False

def format(self, field, expression, output_field=None, *args, **kwargs):
    if not output_field:
        output_field = field + '__alt'
    kwargs = {output_field: expression(field, *args, **kwargs)}
    qs = self.defer(field).annotate(**kwargs)
    return qs

def prefetch_one_level(instances, prefetcher, lookup, level):
    """
    Helper function for prefetch_related_objects

    Runs prefetches on all instances using the prefetcher object,
    assigning results to relevant caches in instance.

    The prefetched objects are returned, along with any additional
    prefetches that must be done due to prefetch_related lookups
    found from default managers.
    """
    # prefetcher must have a method get_prefetch_queryset() which takes a list
    # of instances, and returns a tuple:

    # (queryset of instances of self.model that are related to passed in instances,
    #  callable that gets value to be matched for returned instances,
    #  callable that gets value to be matched for passed in instances,
    #  boolean that is True for singly related objects,
    #  cache name to assign to).

    # The 'values to be matched' must be hashable as they will be used
    # in a dictionary.

    rel_qs, rel_obj_attr, instance_attr, single, cache_name = (
        prefetcher.get_prefetch_queryset(instances, lookup.get_current_queryset(level)))
    # We have to handle the possibility that the QuerySet we just got back
    # contains some prefetch_related lookups. We don't want to trigger the
    # prefetch_related functionality by evaluating the query. Rather, we need
    # to merge in the prefetch_related lookups.
    # Copy the lookups in case it is a Prefetch object which could be reused
    # later (happens in nested prefetch_related).
    additional_lookups = [
        copy.copy(additional_lookup) for additional_lookup
        in getattr(rel_qs, '_prefetch_related_lookups', [])
    ]
    if additional_lookups:
        # Don't need to clone because the manager should have given us a fresh
        # instance, so we access an internal instead of using public interface
        # for performance reasons.
        rel_qs._prefetch_related_lookups = []

    all_related_objects = list(rel_qs)

    is_multi_reference = getattr(rel_qs, 'is_multi_reference', False)

    if not is_multi_reference:
        rel_obj_cache = {}
        for rel_obj in all_related_objects:
            rel_attr_val = rel_obj_attr(rel_obj)
            rel_obj_cache.setdefault(rel_attr_val, []).append(rel_obj)

    to_attr, as_attr = lookup.get_current_to_attr(level)

    # Make sure `to_attr` does not conflict with a field.
    if as_attr and instances:
        # We assume that objects retrieved are homogeneous (which is the premise
        # of prefetch_related), so what applies to first object applies to all.
        model = instances[0].__class__
        try:
            model._meta.get_field(to_attr)
        except exceptions.FieldDoesNotExist:
            pass
        else:
            msg = 'to_attr={} conflicts with a field on the {} model.'
            raise ValueError(msg.format(to_attr, model.__name__))

    for obj in instances:
        instance_attr_val = instance_attr(obj)
        if is_multi_reference:
            vals = [rel_obj for rel_obj in all_related_objects if rel_obj_attr(rel_obj, instance_attr_val)]
        else:
            vals = rel_obj_cache.get(instance_attr_val, [])
        if single:
            val = vals[0] if vals else None
            to_attr = to_attr if as_attr else cache_name
            setattr(obj, to_attr, val)
        else:
            if as_attr:
                setattr(obj, to_attr, vals)
            else:
                # Cache in the QuerySet.all().
                qs = getattr(obj, to_attr).all()
                qs._result_cache = vals
                # We don't want the individual qs doing prefetch_related now,
                # since we have merged this into the current work.
                qs._prefetch_done = True
                obj._prefetched_objects_cache[cache_name] = qs
    return all_related_objects, additional_lookups