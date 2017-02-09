def delete_reverse_related(sender, signal, instance, using, **kwargs):
    for related in instance._meta.related_objects:
        field = related.field
        if getattr(field, 'many_to_many_array', False):
            accessor_name = field.get_reverse_accessor_name()
            accessor = getattr(instance, accessor_name)
            accessor.clear()
