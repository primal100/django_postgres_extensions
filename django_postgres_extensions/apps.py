from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from django.db.models import query
from django.db.models.sql import datastructures
from .models.query import update, _update, format, prefetch_one_level
from .models.sql.datastructures import as_sql
from django.db.models.signals import pre_delete
from .signals import delete_reverse_related
from django.conf import settings


class PSQLExtensionsConfig(AppConfig):
    name = 'django_postgres_extensions'
    verbose_name = _('Extra features for PostgreSQL fields')

    def ready(self):
        query.QuerySet.format = format
        query.QuerySet.update = update
        query.QuerySet._update = _update
        if getattr(settings, 'ENABLE_ARRAY_M2M', False):
            datastructures.Join.as_sql = as_sql
            query.prefetch_one_level = prefetch_one_level
            pre_delete.connect(delete_reverse_related)