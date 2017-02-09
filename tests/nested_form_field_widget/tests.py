import copy
from django.test import TestCase
from django.forms import CharField, Form, TextInput, FileInput
from django_postgres_extensions import forms
from django_postgres_extensions.models.fields import HStoreField

class NestedFormWidgetTest(TestCase):

    def check_html(self, widget, name, value, html='', attrs=None, **kwargs):
        output = widget.render(name, value, attrs=attrs, **kwargs)
        self.assertHTMLEqual(output, html)

    def test_text_inputs(self):
        widget = forms.NestedFormWidget(
            ('A', 'B', 'C'),
            ((TextInput()),
             (TextInput()),
             (TextInput())
             )
        )
        self.check_html(widget, 'name', ['john', 'winston', 'lennon'], html="""<ul>
            <li><label>A:</label><input name="name_a" type="text" value="john" /></li>
            <li><label>B:</label><input name="name_b" type="text" value="winston" /></li>
            <li><label>C:</label><input name="name_c" type="text" value="lennon" /></li>
            </ul>"""
                        )

    def test_constructor_attrs(self):
        widget = forms.NestedFormWidget(
            ('A', 'B', 'C'),
            ((TextInput()),
             (TextInput()),
             (TextInput())
             ),
            attrs={'id': 'bar'},
        )
        self.check_html(widget, 'name', ['john', 'winston', 'lennon'], html="""<ul>
            <li><label for="bar_a">A:</label><input id="bar_a" name="name_a" type="text" value="john" /></li>
            <li><label for="bar_b">B:</label><input id="bar_b" name="name_b" type="text" value="winston" /></li>
            <li><label for="bar_c">C:</label><input id="bar_c" name="name_c" type="text" value="lennon" /></li>
            </ul>
        """
                        )

    def test_needs_multipart_true(self):
        """
        needs_multipart_form should be True if any widgets need it.
        """
        widget = forms.NestedFormWidget(
            ('text', 'file'),
            (TextInput(), FileInput())
        )
        self.assertTrue(widget.needs_multipart_form)

    def test_needs_multipart_false(self):
        """
        needs_multipart_form should be False if no widgets need it.
        """
        widget = forms.NestedFormWidget(
            ('text', 'text2'),
            (TextInput(), TextInput())
        )
        self.assertFalse(widget.needs_multipart_form)

    def test_nested_multiwidget(self):
        """
        NestedFormWidget can be composed of other NestedFormWidgets.
        """
        widget = forms.NestedFormWidget(
            ('A', 'B'),
            (TextInput(), forms.NestedFormWidget(
                ('C', 'D'),
                (TextInput(), TextInput())
                )
             )
        )
        self.check_html(widget, 'name', ['Singer', ['John', 'Lennon']], html=(
            """
            <ul>
            <li><label>A:</label><input name="name_a" type="text" value="Singer" /></li>
            <li><label>B:</label><ul>
            <li><label>C:</label><input name="name_b_c" type="text" value="John" /></li>
            <li><label>D:</label><input name="name_b_d" type="text" value="Lennon" /></li>
            </ul>
            </li>
            </ul>
            """
        ))

    def test_deepcopy(self):
        """
        MultiWidget should define __deepcopy__() (#12048).
        """
        w1 = forms.NestedFormWidget(
            ['A', 'B', 'C'],
            (TextInput(),
             TextInput(),
             TextInput()
             )
        )
        w2 = copy.deepcopy(w1)
        w2.labels.append('d')
        # w2 ought to be independent of w1, since MultiWidget ought
        # to make a copy of its sub-widgets when it is copied.
        self.assertEqual(w1.labels, ['A', 'B', 'C'])


class TestNestedFormField(TestCase):

    def test_valid(self):
        field = forms.NestedFormField(keys=('a', 'b', 'c'))
        value = field.clean(["d", '', "f"])
        self.assertEqual(value, {'a': 'd', 'b': '', 'c': 'f'})

    def test_model_field_formfield_keys(self):
        model_field = HStoreField(keys=('a', 'b', 'c'))
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, forms.NestedFormField)

    def test_model_field_formfield_fields(self):
        model_field = HStoreField(fields=(
                                         ('a', CharField(max_length=10)),
                                         ('b', CharField(max_length=10)),
                                         ('c', CharField(max_length=10))
                                                )
                                        )
        form_field = model_field.formfield()
        self.assertIsInstance(form_field, forms.NestedFormField)

    def test_field_has_changed(self):
        class NestedFormTest(Form):
            f1 = forms.NestedFormField(keys=('a', 'b', 'c'))
        form_w_hstore = NestedFormTest()
        self.assertFalse(form_w_hstore.has_changed())

        form_w_hstore = NestedFormTest({'f1_a': 'd', 'fl_b': 'e', 'f1_c': 'f'})
        self.assertTrue(form_w_hstore.has_changed())

        form_w_hstore = NestedFormTest({'f1_a': 'g'},
                                       initial={'f1_a': 'd', 'fl_b': 'e', 'f1_c': 'f'})
        self.assertTrue(form_w_hstore.has_changed())
