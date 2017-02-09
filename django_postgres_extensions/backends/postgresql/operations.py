from django.db.backends.postgresql.operations import DatabaseOperations as BaseDatabaseOperations

class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_postgres_extensions.models.sql.compiler"