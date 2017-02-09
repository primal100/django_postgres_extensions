from django.db.models import signals
from django.db import transaction, router
from django_postgres_extensions.utils import OrderedSet
from django_postgres_extensions.models.functions import ArrayCat, ArrayRemove, multi_array_remove
from django.utils.functional import cached_property

class MultiReferenceDescriptor(object):

    def __init__(self, rel, reverse=False, isJson=False):
        self.rel = rel
        self.isJson = isJson
        self.reverse = reverse
        self.through = rel.related_model

    def __get__(self, instance, cls=None):
        """
        Get the manager for the many-to-many array field.
        """
        if instance is None:
            return self

        return self.related_manager_cls(instance)

    @cached_property
    def related_manager_cls(self):
        model = self.rel.related_model if self.reverse else self.rel.model
        db = router.db_for_read(model)
        if hasattr(db, 'create_array_many_to_many_manager'):
            create_manager_func = db.create_array_many_to_many_manager
        else:
            create_manager_func = create_array_many_to_many_manager
        return create_manager_func(
            model._default_manager.__class__,
            self.rel,
            self.reverse,
            self.isJson
        )

def create_array_many_to_many_manager(superclass, rel, reverse, IsJson):

    class ArrayForwardManyToManyManager(superclass):

        def __init__(self, instance):
            if instance.pk is None:
                raise ValueError("%r instance needs to have a primary key value before "
                                 "a many-to-many relationship can be used." %
                                 instance.__class__.__name__)
            super(ArrayForwardManyToManyManager, self).__init__()
            self.instance = instance
            self.field = rel.field
            self.target_field = rel.target_field
            self.fieldname = self.field.name
            self.column = self.field.attname
            self.rel = rel
            self.set_attributes()
            self.through = self.rel.related_model

        def __call__(self, **kwargs):
            # We use **kwargs rather than a kwarg argument to enforce the
            # `manager='manager_name'` syntax.
            manager = getattr(self.model, kwargs.pop('manager'))
            if hasattr(self.db, 'create_array_many_to_many_manager'):
                create_manager_func = self.db.create_array_many_to_many_manager
            else:
                create_manager_func = create_array_many_to_many_manager
            manager_class = create_manager_func(manager.__class__, rel, reverse, False)
            return manager_class(instance=self.instance)
        do_not_call_in_templates = True

        def set_attributes(self):
            self.model = self.rel.model
            self.related_model = self.rel.related_model
            self.prefetch_cache_name = rel.field.name
            self.to_field_name = self.target_field.name
            self.core_filters = {'%s' % self.rel.name: self.instance}
            self.symmetrical = self.rel.symmetrical

        def _apply_rel_filters(self, queryset):
            """
            Filter the queryset for the instance this manager is bound to.
            """
            queryset._add_hints(instance=self.instance)
            if self._db:
                queryset = queryset.using(self._db)
            queryset = queryset.filter(**self.core_filters)
            return queryset

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                queryset = super(ArrayForwardManyToManyManager, self).get_queryset()
                return self._apply_rel_filters(queryset)

        def get_prefetch_filters(self, instances):
            pks = []
            for instance in instances:
                pks += getattr(instance, self.column)
            filters = {'%s__in' % self.to_field_name:set(pks)}
            return filters

        def validate_rel_obj(self, rel_obj, fks):
            return getattr(rel_obj, self.to_field_name) in fks

        def get_instance_attr(self, instance):
            return getattr(instance, self.column)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = super(ArrayForwardManyToManyManager, self).get_queryset()

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)

            query = self.get_prefetch_filters(instances)
            queryset = queryset.filter(**query)
            queryset.is_multi_reference = True

            return queryset, self.validate_rel_obj, self.get_instance_attr, False, self.prefetch_cache_name

        def _update_instance(self, **kwargs):
            qs = self.related_model.objects.filter(pk=self.instance.pk)
            qs.update(**kwargs)
        _update_instance.alters_data = True

        def _add_items(self, *objs):
            objs = list(objs)
            if len(objs) == 1:
                exclude = {self.column: objs[0]}
                kwargs = {self.column: ArrayCat(self.column, objs, output_field=self.field)}
                self.related_model.objects.filter(pk=self.instance.pk).exclude(**exclude).update(**kwargs)
            else:
                instance = self.related_model.objects.only(self.column).get(pk=self.instance.pk)
                objs = list(OrderedSet(objs) - set(getattr(instance, self.column)))
                kwargs = {self.column: ArrayCat(self.column, objs, output_field=self.field)}
                self._update_instance(**kwargs)
            # If this is a symmetrical m2m relation to self, add the mirror entry to the other objs array
            if self.symmetrical:
                kwargs = {self.column: ArrayCat(self.column, [self.instance.pk], output_field=self.field)}
                self.model.objects.filter(pk__in=objs).update(**kwargs)
        _add_items.alters_data = True

        def validate_item(self, obj):
            return self.field.validate_item(obj, model=self.model)

        def add(self, *objs, **kwargs):
            objs = [self.validate_item(obj) for obj in objs]
            signals.m2m_changed.send(
                sender=self.through, action='pre_add',
                instance=self.instance, reverse=self.reverse,
                model=self.model, pk_set=objs, using=self.db,
            )
            with transaction.atomic():
                self._add_items(*objs)
            signals.m2m_changed.send(
                sender=self.through, action='post_add',
                instance=self.instance, reverse=self.reverse,
                model=self.model, pk_set=objs, using=self.db,
            )

        def remove(self, *objs):
            objs = [self.validate_item(obj) for obj in objs]
            signals.m2m_changed.send(
                sender=self.through, action="pre_remove",
                instance=self.instance, reverse=self.reverse,
                model=self.model, pk_set=objs, using=self.db,
            )
            with transaction.atomic():
                self._remove_items(*objs)
            signals.m2m_changed.send(
                sender=self.through, action="post_remove",
                instance=self.instance, reverse=self.reverse,
                model=self.model, pk_set=objs, using=self.db,
            )
        remove.alters_data = True

        def _remove_items(self, *objs, **kwargs):
            if objs:
                chunks = [objs[x:x + 100] for x in range(0, len(objs), 100)]
                for chunk in chunks:
                    kwargs = {self.column: multi_array_remove(self.column, *chunk)}
                self._update_instance(**kwargs)
                # If this is a symmetrical m2m relation to self, add the mirror entry to the other objs array
                if self.symmetrical:
                    kwargs = {self.column: ArrayRemove(self.column, self.instance.pk, output_field=self.field)}
                    self.model.objects.filter(pk__in=list(objs)).update(**kwargs)
        _remove_items.alters_data = True

        def create(self, **kwargs):
            new_obj = super(ArrayForwardManyToManyManager, self).create(**kwargs)
            self.add(new_obj)
            return new_obj
        create.alters_data = True

        def get_or_create(self, **kwargs):
            obj, created = super(ArrayForwardManyToManyManager, self).get_or_create(**kwargs)
            # We only need to add() if created because if we got an object back
            # from get() then the relationship already exists.
            if created:
                self.add(obj)
            return obj, created
        get_or_create.alters_data = True

        def update_or_create(self, **kwargs):
            obj, created = super(ArrayForwardManyToManyManager, self).update_or_create(**kwargs)
            # We only need to add() if created because if we got an object back
            # from get() then the relationship already exists.
            if created:
                self.add(obj)
            return obj, created
        update_or_create.alters_data = True

        def _clear(self):
            kwargs = {self.column: []}
            self._update_instance(**kwargs)
            if self.symmetrical:
                kwargs = {self.column: ArrayRemove(self.column, self.instance.pk, output_field=self.field)}
                self.model.objects.update(**kwargs)
        _clear.alters_data = True

        def clear(self, **kwargs):
            with transaction.atomic():
                signals.m2m_changed.send(
                    sender=self.through, action="pre_clear",
                    instance=self.instance, reverse=reverse,
                    model=self.model, pk_set=None, using=self.db,
                )
                with transaction.atomic():
                    self._clear()
                signals.m2m_changed.send(
                    sender=self.model, action="post_clear",
                    instance=self.instance, reverse=reverse,
                    model=self.model, pk_set=None, using=self.db,
                )
        clear.alters_data = True

        def set(self, objs, **kwargs):
            with transaction.atomic(savepoint=False):
                old_ids = set(self.values_list(self.to_field_name, flat=True))
                new_objs = []
                for obj in objs:
                    fk_val = (obj.pk if isinstance(obj, self.model) else obj)
                    if fk_val in old_ids:
                        old_ids.remove(fk_val)
                    else:
                        new_objs.append(obj)
                self.remove(*old_ids)
                self.add(*new_objs)
        set.alters_data = True

    class ArrayReverseManyToManyManager(ArrayForwardManyToManyManager):

        def set_attributes(self):
            self.model = rel.related_model
            self.related_model = rel.model
            self.prefetch_cache_name = rel.field.related_query_name()
            self.core_filters = {'%s' % self.fieldname: self.instance}
            self.prefetch_filters = {}
            self.to_field_name = 'pk'
            self.to_field_value = self.instance.pk
            self.symmetrical = False

        def validate_rel_obj(self, rel_obj, pk):
            return pk in getattr(rel_obj, self.column)

        def get_instance_attr(self, instance):
            return getattr(instance, self.to_field_name)

        def get_prefetch_filters(self, instances):
            filters = {'%s__overlap' % self.fieldname: instances}
            return filters

        def _add_items(self, *objs, **kwargs):
            exclude = {self.column: self.instance.pk}
            qs = self.model.objects.filter(pk__in = objs).exclude(**exclude)
            kwargs = {self.column: ArrayCat(self.column, [self.to_field_value])}
            qs.update(**kwargs)
        _add_items.alters_data = True

        def _remove_items(self, *objs, **kwargs):
            qs = self.filter(pk__in = objs)
            kwargs = {self.column: ArrayRemove(self.column, self.to_field_value)}
            with transaction.atomic():
                qs.update(**kwargs)
        _remove_items.alters_data = True

        def _clear(self):
            with transaction.atomic():
                kwargs = {self.column: ArrayRemove(self.column, self.to_field_value)}
            self.model.objects.update(**kwargs)
        _clear.alters_data = True

    if reverse:
        return ArrayReverseManyToManyManager
    return ArrayForwardManyToManyManager