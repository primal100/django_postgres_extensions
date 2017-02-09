from __future__ import unicode_literals

from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils.html import format_html
import copy

class NestedFormWidget(widgets.MultiWidget):
    """
    A widget that is composed of multiple widgets with labels in a list.

    Its render() method differs from the MultiWidget in that it adds support for labels
    and presents the widgets in a list.

    For initial values, the decompress method expects a dictionary of key names and values.
    The widget's value_from_datadict method returns an array of values.

    Its render() method differs from the MultiWidget in that it adds support for labels
    and presents the widgets in a list. It deals with widget labels which may be different
    from the key names for that widget.

    The ``labels`` argument is a list/tuple of label names which will also be used for css names and ids.
    The ``widgets`` arguments is a list of widgets. Labels will be matched to widget by index.
    The optional ``names`` argument is a dictionary of labels to names. The name refers to the key name in the
    python dictionary given to the decompress method. If this argument is not given, labels and key names
    will be assumed to be the same.

    You'll probably want to use this class with NestedFormField.
    """
    def __init__(self, labels, widgets, names=None, attrs=None):
        self.labels = labels
        if names:
            self.names = names
        else:
            self.names = {label: label for label in labels}
        self.id_names = [label.lower().replace(" ", "") for label in labels]
        super(NestedFormWidget, self).__init__(widgets, attrs=attrs)

    def render(self, name, value, attrs=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = ["<ul>\n"]
        final_attrs = self.build_attrs(attrs)
        base_id_ = final_attrs.get('id')
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            label = self.labels[i]
            id_name = self.id_names[i]
            if base_id_:
                id_ = '%s_%s' % (base_id_, id_name)
                final_attrs = dict(final_attrs, id=id_)
                if widget.id_for_label:
                    label_for = format_html(' for="{}"', widget.id_for_label(id_))
                else:
                    label_for = ''
            else:
                label_for = ''
            output.append(format_html(
                '<li><label{}>{}</label>', label_for, label + ':'))
            output.append(widget.render(name + '_%s' % id_name, widget_value, final_attrs) + '</li>\n')
        output.append("</ul>\n")
        return mark_safe(self.format_output(output))

    def value_from_datadict(self, data, files, name):
        return [widget.value_from_datadict(data, files, "%s_%s" % (name, self.id_names[i])) for i, widget in
                enumerate(self.widgets)]

    def decompress(self, value):
        if not value:
            return []
        values = [value[self.names[label]] for label in self.labels]
        return values

    def value_omitted_from_data(self, data, files, name):
        return False

    def __deepcopy__(self, memo):
        obj = super(NestedFormWidget, self).__deepcopy__(memo)
        obj.labels = copy.deepcopy(self.labels)
        return obj