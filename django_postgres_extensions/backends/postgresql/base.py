from django.db.backends.postgresql.base import DatabaseWrapper as BaseDatabaseWrapper
from .schema import DatabaseSchemaEditor
from .creation import DatabaseCreation
from .operations import DatabaseOperations

class DatabaseWrapper(BaseDatabaseWrapper):

    SchemaEditorClass = DatabaseSchemaEditor

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = DatabaseCreation(self)
        self.ops = DatabaseOperations(self)

        self.any_operators = {
            'exact': '= ANY(%s)',
            'in': 'LIKE ANY(%s)',
            'gt': '< ANY(%s)',
            'gte': '<= ANY(%s)',
            'lt': '> ANY(%s)',
            'lte': '>= ANY(%s)',
            'startof': 'LIKE ANY(%s)',
            'endof': 'LIKE ANY(%s)',
            'contains': '<@ ANY(%s)'
        }


        self.all_operators = {
            'exact': '= ALL(%s)',
            'in': 'LIKE ALL(%s)',
            'gt': '< ALL(%s)',
            'gte': '<= ALL(%s)',
            'lt': '> ALL(%s)',
            'lte': '>= ALL(%s)',
            'startof': 'LIKE ALL(%s)',
            'endof': 'LIKE ALL(%s)',
            'contains': '<@ ALL(%s)'
        }
