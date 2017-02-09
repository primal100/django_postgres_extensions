from django.contrib.admin.options import ModelAdmin
from django.utils.translation import string_concat, ugettext as _
from django.forms.widgets import CheckboxSelectMultiple, SelectMultiple
from django_postgres_extensions.models import ArrayManyToManyField
from django.contrib.admin import widgets

class PostgresAdmin(ModelAdmin):

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        Get a form Field for a ManyToManyField.
        """
        # If it uses an intermediary model that isn't auto created, don't show
        # a field in admin.
        if hasattr(db_field, 'through') and not db_field.remote_field.through._meta.auto_created:
            return None
        db = kwargs.get('using')

        if db_field.name in self.raw_id_fields:
            kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.remote_field,
                                    self.admin_site, using=db)
            kwargs['help_text'] = ''
        elif db_field.name in (list(self.filter_vertical) + list(self.filter_horizontal)):
            kwargs['widget'] = widgets.FilteredSelectMultiple(
                db_field.verbose_name,
                db_field.name in self.filter_vertical
            )

        if 'queryset' not in kwargs:
            queryset = self.get_field_queryset(db, db_field, request)
            if queryset is not None:
                kwargs['queryset'] = queryset

        form_field = db_field.formfield(**kwargs)
        if isinstance(form_field.widget, SelectMultiple) and not isinstance(form_field.widget, CheckboxSelectMultiple):
            msg = _('Hold down "Control", or "Command" on a Mac, to select more than one.')
            help_text = form_field.help_text
            form_field.help_text = string_concat(help_text, ' ', msg) if help_text else msg
        return form_field

    def formfield_for_dbfield(self, db_field, request, **kwargs):

        # ForeignKey or ManyToManyFields
        if isinstance(db_field, ArrayManyToManyField):
            # Combine the field kwargs with any options for formfield_overrides.
            # Make sure the passed in **kwargs override anything in
            # formfield_overrides because **kwargs is more specific, and should
            # always win.
            if db_field.__class__ in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[db_field.__class__], **kwargs)

            formfield = self.formfield_for_manytomany(db_field, request, **kwargs)

            # For non-raw_id fields, wrap the widget with a wrapper that adds
            # extra HTML -- the "add other" interface -- to the end of the
            # rendered output. formfield can be None if it came from a
            # OneToOneField with parent_link=True or a M2M intermediary.
            if formfield and db_field.name not in self.raw_id_fields:
                related_modeladmin = self.admin_site._registry.get(db_field.remote_field.model)
                wrapper_kwargs = {}
                if related_modeladmin:
                    wrapper_kwargs.update(
                        can_add_related=related_modeladmin.has_add_permission(request),
                        can_change_related=related_modeladmin.has_change_permission(request),
                        can_delete_related=related_modeladmin.has_delete_permission(request),
                    )
                formfield.widget = widgets.RelatedFieldWidgetWrapper(
                    formfield.widget, db_field.remote_field, self.admin_site, **wrapper_kwargs
                )

            return formfield
        else:
            return super(PostgresAdmin, self).formfield_for_dbfield(db_field, request, **kwargs)