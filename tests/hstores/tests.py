from __future__ import unicode_literals

from django.test import TestCase
from .models import Product
from django_postgres_extensions.models.functions import *
from django_postgres_extensions.models.expressions import Key, Keys
from django.db.utils import ProgrammingError
from django.db import transaction


class HStoreIndexTests(TestCase):

    def setUp(self):
        super(HStoreIndexTests, self).setUp()
        self.product = Product(name='xyz', description={'Industry': 'Music', 'Release': 'Album', 'Genre': 'Rock'})
        self.product.save()
        self.queryset = Product.objects.filter(pk=self.product.pk)

    def tearDown(self):
        Product.objects.all().delete()

    def test_hstore_value(self):
        product = self.queryset.get()
        self.assertDictEqual(product.description, {'Industry': 'Music', 'Release': 'Album', 'Genre': 'Rock'})

    def test_hstore_value_by_key(self):
        with transaction.atomic():
            obj = self.queryset.annotate(Key('description', 'Release')).get()
        self.assertEqual(obj.description__Release, 'Album')

    def test_hstore_values_by_keys(self):
        with transaction.atomic():
            obj = self.queryset.annotate(Keys('description', ['Industry', 'Release'])).get()
        self.assertListEqual(obj.description__selected, ['Music', 'Album'])

    def test_array_update_keys_values(self):
        with transaction.atomic():
            self.queryset.update(description__ = {'Genre': 'Heavy Metal', 'Popularity': 'Very Popular'})
        product = self.queryset.get()
        self.assertDictEqual(product.description, {'Industry': 'Music', 'Release': 'Album', 'Genre': 'Heavy Metal',
                                                   'Popularity': 'Very Popular'})

    def test_hstore_raw_int_raises(self):
        with transaction.atomic():
            self.queryset.update(description__={'Popularity': 5})
            self.assertRaises(ProgrammingError, self.queryset.update,
                              description__raw={'Popularity': 5})

class HstoreFuncTests(TestCase):
    def setUp(self):
        super(HstoreFuncTests, self).setUp()
        self.product = Product(name='xyz', description={'Industry': 'Music', 'Release': 'Album', 'Genre': 'Rock', 'Rating': '8'},
                               details={'Popularity': 'Very Popular'})
        self.product.save()
        self.queryset = Product.objects.filter(pk=self.product.pk)

    def tearDown(self):
        Product.objects.all().delete()

    def test_hstore_new(self):
        product = Product(name='xyz', description=HStore(['Industry', 'Release', 'Genre', 'Popularity'],
                                                         ['Film', 'Movie', 'Horror', 'Very Good']))
        product.save()
        queryset = Product.objects.filter(id=product.id)
        obj = queryset.get()
        self.assertDictEqual(obj.description,
                             {'Genre': 'Horror', 'Release': 'Movie', 'Industry': 'Film', 'Popularity': 'Very Good'})

    def test_hstore_slice(self):
        with transaction.atomic():
            obj = self.queryset.annotate(description_slice=Slice('description', ['Industry', 'Release'])).get()
        self.assertDictEqual(obj.description_slice,  {'Release': 'Album', 'Industry': 'Music'})

    def test_hstore_delete_key(self):
        with transaction.atomic():
            self.queryset.update(description = Delete('description', 'Genre'))
        product = self.queryset.get()
        self.assertDictEqual(product.description, {'Industry': 'Music', 'Release': 'Album', 'Rating': '8'})

    def test_hstore_delete_keys(self):
        with transaction.atomic():
            self.queryset.update(description = Delete('description', ['Industry', 'Genre']))
        product = self.queryset.get()
        self.assertDictEqual(product.description, {'Release': 'Album', 'Rating': '8'})

    def test_hstore_delete_by_dict(self):
        with transaction.atomic():
            self.queryset.update(description=Delete('description', {'Industry': 'Music', 'Release': 'Song', 'Genre': 'Rock'}))
        product = self.queryset.get()
        self.assertDictEqual(product.description, {'Release': 'Album', 'Rating': '8'})

    def test_hstore_keys_as_array(self):
        with transaction.atomic():
            product = self.queryset.annotate(description_keys=AKeys('description')).get()
        keys = product.description_keys
        keys.sort()
        self.assertListEqual(keys, ['Genre', 'Industry', 'Rating', 'Release'])

    def test_hstore_values_as_array(self):
        with transaction.atomic():
            product = self.queryset.annotate(description_values=AVals('description')).get()
        values = product.description_values
        values.sort()
        self.assertListEqual(values, ['8', 'Album', 'Music', 'Rock'])

    def test_hstore_to_array(self):
        with transaction.atomic():
            product = self.queryset.annotate(description_array=HStoreToArray('description')).get()
        self.assertListEqual(product.description_array, ['Genre', 'Rock', 'Rating', '8', 'Release', 'Album', 'Industry', 'Music'])

    def test_hstore_to_matrix(self):
        with transaction.atomic():
            product = self.queryset.annotate(description_matrix=HStoreToMatrix('description')).get()
        self.assertListEqual(product.description_matrix, [['Genre', 'Rock'], ['Rating', '8'], ['Release', 'Album'], ['Industry', 'Music']])

    def test_hstore_to_jsonb(self):
        with transaction.atomic():
            product = self.queryset.annotate(description_jsonb=HstoreToJSONB('description')).get()
        self.assertDictEqual(product.description_jsonb,
                             {'Genre': 'Rock', 'Release': 'Album', 'Industry': 'Music', 'Rating': "8"})

    def test_hstore_to_jsonb_loose(self):
        with transaction.atomic():
            product = self.queryset.annotate(description_jsonb=HstoreToJSONBLoose('description')).get()
        self.assertDictEqual(product.description_jsonb,
                             {'Genre': 'Rock', 'Release': 'Album', 'Industry': 'Music', 'Rating': 8})

    def test_queryset_format(self):
        with transaction.atomic():
            qs = self.queryset.format('description', HstoreToJSONBLoose)
            product = qs.get()
        self.assertDictEqual(product.description__alt,
                         {'Genre': 'Rock', 'Release': 'Album', 'Industry': 'Music', 'Rating': 8})