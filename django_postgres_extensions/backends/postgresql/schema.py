from django.db.backends.postgresql import schema

class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):
    sql_create_array_index = "CREATE INDEX %(name)s ON %(table)s USING GIN (%(columns)s)%(extra)s"

    def _model_indexes_sql(self, model):
        output = super(DatabaseSchemaEditor, self)._model_indexes_sql(model)
        if not model._meta.managed or model._meta.proxy or model._meta.swapped:
            return output

        for field in model._meta.local_fields:
            array_index_statement = self._create_array_index_sql(model, field)
            if array_index_statement is not None:
                output.append(array_index_statement)
        return output

    def _create_array_index_sql(self, model, field):
        db_type = field.db_type(connection=self.connection)
        if db_type is not None and '[' in db_type and db_type.endswith(']') and (field.db_index or field.unique):
            return self._create_index_sql(model, [field], suffix='_gin', sql=self.sql_create_array_index)
        return None