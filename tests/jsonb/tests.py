from __future__ import unicode_literals, absolute_import

from django.test import TestCase
from .models import Product
from django_postgres_extensions.models.functions import *
from django_postgres_extensions.models.expressions import Key
from psycopg2.extras import Json
from django.db import transaction

class JSONIndexTests(TestCase):

    def setUp(self):
        super(JSONIndexTests, self).setUp()
        self.product = Product(name='xyz', description={'Industry': 'Music', 'Details': {'Release': 'Album', 'Genre': 'Rock', 'Rating': 8}, 'Price': 9.99, 'Tags': ['Heavy', 'Guitar']})
        self.product.save()
        self.queryset = Product.objects.filter(pk=self.product.pk)
        self.pk_queryset = self.queryset.only('id')

    def tearDown(self):
        Product.objects.all().delete()

    def test_json_value(self):
        product = self.queryset.get()
        self.assertDictEqual(product.description,
                             {'Industry': 'Music', 'Details': {'Release': 'Album', 'Genre': 'Rock', 'Rating': 8},
                              'Price': 9.99, 'Tags': ['Heavy', 'Guitar']})

    def test_json_value_by_key(self):
        with transaction.atomic():
            obj = self.pk_queryset.annotate(Key('description', 'Details')).get()
        self.assertDictEqual(obj.description__Details, {'Genre': 'Rock', 'Rating': 8, 'Release': 'Album'})

    def test_json_value_by_key_path(self):
        with transaction.atomic():
            obj = self.pk_queryset.annotate(Key('description', 'Details__Rating')).get()
        self.assertEqual(obj.description__Details__Rating, 8)
        with transaction.atomic():
            obj = self.pk_queryset.annotate(Key('description', 'Tags__1')).get()
        self.assertEqual(obj.description__Tags__1, "Guitar")

    def test_json_update_keys_values(self):
        with transaction.atomic():
            self.queryset.update(description__ = {'Industry': 'Movie', 'Popularity': 'Very Popular'})
        product = self.queryset.get()
        self.assertDictEqual(product.description,
                             {'Industry': 'Movie', 'Details': {'Release': 'Album', 'Genre': 'Rock', 'Rating': 8},
                              'Price': 9.99, 'Popularity': 'Very Popular', 'Tags': ['Heavy', 'Guitar']})

    def test_json_update_delete_key(self):
        with transaction.atomic():
            self.queryset.update(description__del ='Details')
        product = self.queryset.get()
        self.assertDictEqual(product.description,
                                {'Industry': 'Music', 'Price': 9.99, 'Tags': ['Heavy', 'Guitar']})

    def test_json_update_delete_key_path(self):
        with transaction.atomic():
            self.queryset.update(description__del = 'Details__Release')
        product = self.queryset.get()
        self.assertDictEqual(product.description,
                             {'Industry': 'Music', 'Details': {'Genre': 'Rock', 'Rating': 8},
                              'Price': 9.99, 'Tags': ['Heavy', 'Guitar']})
        with transaction.atomic():
            self.queryset.update(description__del='Tags__1')
        product = self.queryset.get()
        self.assertDictEqual(product.description,
                             {'Industry': 'Music', 'Details': {'Genre': 'Rock', 'Rating': 8},
                              'Price': 9.99, 'Tags': ['Heavy']})

class JSONFuncTests(TestCase):
    def setUp(self):
        super(JSONFuncTests, self).setUp()
        self.product = Product(name='xyz', description={'Industry': 'Music', 'Details': {'Release': 'Album', 'Genre': 'Rock', 'Rating': 8}, 'Price': 9.99, 'Tags': ['Heavy', 'Guitar']})
        self.product.save()
        self.queryset = Product.objects.filter(pk=self.product.pk)
        self.product2 = Product(name='xyz', description=[{'a': 'b', 'c':'d'}, {'a': 'e', 'c': 'f'}])
        self.product2.save()
        self.queryset2 = Product.objects.filter(pk=self.product2.pk)

    def tearDown(self):
        Product.objects.all().delete()

    def test_jsonb_set(self):
        with transaction.atomic():
            self.queryset.update(description = JSONBSet('description', ['Details', 'Genre'], Json('Heavy Metal'), True))
        obj = self.queryset.get()
        self.assertDictEqual(obj.description,
                             {'Price': 9.99, 'Industry': 'Music', 'Details': {'Genre': 'Heavy Metal', 'Release': 'Album', 'Rating': 8}, 'Tags': ['Heavy', 'Guitar']})

    def test_jsonb_array_set(self):
        with transaction.atomic():
            self.queryset2.update(description=JSONBSet('description', ['1', 'c'], Json('g')))
        obj = self.queryset2.get()
        self.assertListEqual(obj.description,
                             [{'a': 'b', 'c': 'd'}, {'a': 'e', 'c': 'g'}])

    def test_jsonb_array_length(self):
        with transaction.atomic():
            qs = self.queryset2.format('description', JSONBArrayLength, output_field='desc_length')
            obj = qs.get()
        self.assertEqual(obj.desc_length, 2)