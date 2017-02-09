from django.db.models.sql.subqueries import UpdateQuery as BaseUpdateQuery
from django.db.utils import six
from django.core.exceptions import FieldError

class UpdateQuery(BaseUpdateQuery):
    def add_update_values(self, values):
        """
        Convert a dictionary of field name to value mappings into an update
        query. This is the entry point for the public update() method on
        querysets.
        """
        values_seq = []
        for name, val in six.iteritems(values):
            if '__' in name:
                indexes = name.split('__')
                field_name = indexes.pop(0)
                field = self.get_meta().get_field(field_name)
                val = field.get_update_type(indexes, val)
                model = field.model
            else:
                field = self.get_meta().get_field(name)
                direct = not (field.auto_created and not field.concrete) or not field.concrete
                model = field.model._meta.concrete_model
                if not direct or (field.is_relation and field.many_to_many):
                    raise FieldError(
                        'Cannot update model field %r (only non-relations and '
                        'foreign keys permitted).' % field
                    )
                else:
                    if model is not self.get_meta().model:
                        self.add_related_update(model, field, val)
                        continue
            values_seq.append((field, model, val))
        return self.add_update_fields(values_seq)