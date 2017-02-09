from __future__ import unicode_literals

from django.test import TestCase
from .models import Product
from django_postgres_extensions.models.functions import *
from django_postgres_extensions.models.expressions import F, Value as V, Index, SliceArray
from django.db.utils import ProgrammingError, DataError
from django.db import transaction
from unittest import skip

class ArrayCharsIndexTests(TestCase):

    def setUp(self):
        super(ArrayCharsIndexTests, self).setUp()
        self.product = Product(name='xyz', tags=['Music', 'Album', 'Rock'], moretags=['Very Popular'])
        self.product.save()
        self.queryset = Product.objects.filter(pk=self.product.pk)
        obj = Product.objects.annotate(Index('tags', 1)).get()

    def tearDown(self):
        self.queryset.delete()

    def test_array_values(self):
        product = self.queryset.get()
        array_values = product.tags
        self.assertListEqual(array_values, ['Music', 'Album', 'Rock'])

    def test_array_index(self):
        with transaction.atomic():
            obj = self.queryset.annotate(Index('tags', 1)).get()
        self.assertEqual(obj.tags__1, 'Album')

    def test_array_index_with_output_field(self):
        with transaction.atomic():
            obj = self.queryset.annotate(tag_1=Index('tags', 1)).get()
        self.assertEqual(obj.tag_1, 'Album')

    def test_array_index_slice(self):
        with transaction.atomic():
            obj = self.queryset.annotate(SliceArray('tags', 0, 1)).get()
        self.assertEqual(obj.tags__0_1, ['Music', 'Album'])

    def test_array_update_index(self):
        with transaction.atomic():
            self.queryset.update(tags__2='Heavy Metal')
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Heavy Metal'])

    def test_array_int_converted(self):
        with transaction.atomic():
            self.queryset.update(tags__2=1)
            product = self.queryset.get()
            self.assertListEqual(product.tags, ['Music', 'Album', '1'])

class ArrayCharsFuncTests(TestCase):
    def setUp(self):
        super(ArrayCharsFuncTests, self).setUp()
        self.product = Product(name='xyz', tags=['Music', 'Album', 'Rock'], moretags=['Very Popular'])
        self.product.save()
        self.queryset = Product.objects.filter(id=self.product.id)

    def tearDown(self):
        self.queryset.delete()

    def test_array_length(self):
        with transaction.atomic():
            obj = self.queryset.annotate(tags_length=ArrayLength('tags', 1)).get()
        self.assertEqual(obj.tags_length, 3)

    def test_array_append(self):
        with transaction.atomic():
            obj = self.queryset.annotate(tags_appended=ArrayAppend('tags', 'Popular')).get()
        self.assertListEqual(obj.tags_appended, ['Music', 'Album', 'Rock', 'Popular'])
        with transaction.atomic():
            self.queryset.update(tags = ArrayAppend('tags', 'Popular'))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Rock', 'Popular'])

    def test_array_char_raises(self):
        with transaction.atomic():
            self.assertRaises(ProgrammingError, self.queryset.update, tags=ArrayAppend('tags', 1))

    def test_array_prepend(self):
        with transaction.atomic():
            self.queryset.update(tags = ArrayPrepend('Popular', 'tags'))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Popular', 'Music', 'Album', 'Rock'])

    def test_array_remove(self):
        with transaction.atomic():
            self.queryset.update(tags = ArrayRemove('tags', 'Album'))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Rock'])

    def test_array_cat(self):
        with transaction.atomic():
            self.queryset.update(tags = ArrayCat('tags', 'moretags'))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Rock', 'Very Popular'])

    def test_array_cat_list(self):
        with transaction.atomic():
            self.queryset.update(tags=ArrayCat('tags', ['Popular', '8'], output_field=Product._meta.get_field('tags')))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Rock', 'Popular', '8'])

    def test_array_replace(self):
        with transaction.atomic():
            self.queryset.update(tags = ArrayReplace('tags', 'Rock', 'Heavy Metal'))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Heavy Metal'])

    def test_array_position(self):
        with transaction.atomic():
            obj = self.queryset.annotate(position=ArrayPosition('tags', 'Rock')).get()
        self.assertEqual(obj.position, 3)

    def test_array_positions(self):
        with transaction.atomic():
            self.queryset.update(tags = ArrayPrepend('Rock', 'tags'))
        with transaction.atomic():
            obj = self.queryset.annotate(positions=ArrayPositions('tags', 'Rock')).get()
        self.assertEqual(obj.positions, [1, 4])

class ArrayCharsCatTests(TestCase):
    def setUp(self):
        super(ArrayCharsCatTests, self).setUp()
        self.product = Product(name='xyz', tags=['Music', 'Album', 'Rock'], moretags=['Very Popular'])
        self.product.save()
        self.queryset = Product.objects.filter(id=self.product.id)
        self.prod1_queryset = self.queryset.filter(id=self.product.id)

    def tearDown(self):
        self.queryset.delete()

    def test_array_cat_append(self):
        with transaction.atomic():
            self.queryset.update(tags=F('tags').cat(V(['Popular'], output_field = Product._meta.get_field('tags'))))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Rock', 'Popular'])

    def test_array_cat_arrays(self):
        with transaction.atomic():
            self.queryset.update(tags=F('tags').cat(F('moretags')))
        product = self.queryset.get()
        self.assertListEqual(product.tags, ['Music', 'Album', 'Rock', 'Very Popular'])

    def test_array_char_raises(self):
        with transaction.atomic():
            self.assertRaises((ProgrammingError), self.queryset.update, tags=F('tags').cat(V(1)))

class ArrayIntTests(TestCase):
    def setUp(self):
        super(ArrayIntTests, self).setUp()
        self.product = Product(name='xyz', prices=[0, 1, 2])
        self.product.save()
        self.queryset = Product.objects.filter(id=self.product.id)

    def test_array_int_index(self):
        with transaction.atomic():
            obj = self.queryset.annotate(Index('prices', 1)).get()
        self.assertEqual(obj.prices__1, 1)

    def test_array_int_update_index(self):
        with transaction.atomic():
            self.queryset.update(prices__2=3)
        product = self.queryset.get()
        self.assertListEqual(product.prices, [0, 1, 3])

    def test_array_int_append(self):
        with transaction.atomic():
            self.queryset.update(prices=ArrayAppend('prices', 3))
        product = self.queryset.get()
        self.assertListEqual(product.prices, [0, 1, 2, 3])

    def test_array_int_cat_append(self):
        with transaction.atomic():
            self.queryset.update(prices=F('prices').cat(V(3)))
        product = self.queryset.get()
        self.assertListEqual(product.prices, [0,1,2,3])

    def test_array_int_cat_append_list(self):
        with transaction.atomic():
            self.queryset.update(prices=F('prices').cat(V([3, 4])))
        product = self.queryset.get()
        self.assertListEqual(product.prices, [0,1,2, 3, 4])

    def test_array_int_cat_prepend(self):
        with transaction.atomic():
            self.queryset.update(prices=V(-1).cat(F('prices')))
        product = self.queryset.get()
        self.assertListEqual(product.prices, [-1, 0, 1, 2])

    def test_array_int_double_cat(self):
        with transaction.atomic():
            self.queryset.update(prices=V(-1).cat(F('prices').cat(V(3))))
        product = self.queryset.get()
        self.assertListEqual(product.prices, [-1, 0, 1, 2, 3])

    def test_array_int_raises(self):
        self.assertRaises(DataError, self.queryset.update, prices=ArrayAppend('prices', 'test'))

class ArrayMultiDimensionalTests(TestCase):
    def setUp(self):
        super(ArrayMultiDimensionalTests, self).setUp()
        self.product = Product(name='xyz', coordinates=[[0,15, 25], [15,30, 40], [45, 60, 90]])
        self.product.save()
        self.queryset = Product.objects.filter(id=self.product.id)

    def tearDown(self):
        self.queryset.delete()

    def test_2d_array_values(self):
        product = self.queryset.get()
        array_values = product.coordinates
        self.assertListEqual(array_values, [[0,15, 25], [15, 30, 40], [45, 60, 90]])

    def test_2d_array_dimensions(self):
        with transaction.atomic():
            obj = self.queryset.annotate(coordinates_dims = ArrayDims('coordinates')).get()
        self.assertEqual(obj.coordinates_dims, '[1:3][1:3]')

    def test_2d_array_upper(self):
        with transaction.atomic():
            obj = self.queryset.annotate(coordinates_upper_1 = ArrayUpper('coordinates', 1)).get()
        self.assertEqual(obj.coordinates_upper_1, 3)

    def test_2d_array_lower(self):
        with transaction.atomic():
            obj = self.queryset.annotate(coordinates_lower_2 = ArrayLower('coordinates', 2)).get()
        self.assertEqual(obj.coordinates_lower_2, 1)

    def test_2d_array_length(self):
        with transaction.atomic():
            obj = self.queryset.annotate(coordinates_length_2=ArrayLength('coordinates', 2)).get()
        self.assertEqual(obj.coordinates_length_2, 3)

    def test_2d_array_cardinality(self):
        with transaction.atomic():
            obj = self.queryset.annotate(coordinates_cardinality=Cardinality('coordinates')).get()
        self.assertEqual(obj.coordinates_cardinality, 9)

    def test_2d_array_index(self):
        with transaction.atomic():
            obj = self.queryset.annotate(Index(Index('coordinates', 2), 1)).get()
        self.assertEqual(obj.coordinates__2__1, 60)

    def test_2d_array_index_slice_1(self):
        with transaction.atomic():
            obj = self.queryset.annotate(SliceArray(SliceArray('coordinates', 0, 2), 0, 0)).get()
        self.assertEqual(obj.coordinates__0_2__0_0, [[0], [15], [45]])
        with transaction.atomic():
            obj = self.queryset.annotate(SliceArray(SliceArray('coordinates', 0, 2), 1, 1)).get()
        self.assertEqual(obj.coordinates__0_2__1_1, [[15], [30], [60]])

    def test_2d_array_index_slice_2(self):
        with transaction.atomic():
            obj = self.queryset.annotate(SliceArray(SliceArray('coordinates', 1, 1), 1, 2)).get()
        self.assertEqual(obj.coordinates__1_1__1_2, [[30, 40]])

    def test_2d_array_index_slice_3(self):
        with transaction.atomic():
            obj = self.queryset.annotate(SliceArray(SliceArray('coordinates', 1, 2), 1, 2)).get()
        self.assertEqual(obj.coordinates__1_2__1_2, [[30, 40], [60, 90]])

    @skip("Update seems to run but change is not made '{'")
    def test_2d_array_update_index_1(self):
        with transaction.atomic():
            self.queryset.update(tags__1=[70, 90, 100])
        product = self.queryset.get()
        self.assertListEqual(product.coordinates, [[0,15, 25], [70, 90, 100], [45, 60, 90]])

    @skip("Update seems to run but unable to retrieve object due to DataError: array does not start with '{'")
    def test_2d_array_update_index_2(self):
        with transaction.atomic():
            self.queryset.update(tags__1__2=35)
        product = self.queryset.get()
        self.assertListEqual(product.coordinates, [[0,15, 25], [15, 35, 40], [45, 60, 90]])

    @skip("Fails with 'No function matches the given name and argument types. You might need to add explicit type casts.'")
    def test_2d_array_append_1(self):
        with transaction.atomic():
            obj = self.queryset.annotate(coordinates_appended=ArrayAppend('coordinates', [70, 90, 100])).get()
        self.assertListEqual(obj.coordinates_appended, [[0,15, 25], [15, 35, 40], [45, 60, 90], [70, 90, 100]])
        with transaction.atomic():
            self.queryset.update(coordinates=ArrayAppend('coordinates', [70, 90, 100]))
        product = self.queryset.get()
        self.assertListEqual(product.coordinates, [[0,15, 25], [15, 35, 40], [45, 60, 90], [70, 90, 100]])

    @skip(
        "Fails with 'No function matches the given name and argument types. "
        "You might need to add explicit type casts.'")
    def test_2d_array_append_2(self):
        with transaction.atomic():
            obj = self.queryset.update(coordinates=ArrayAppend(Index('coordinates', 1), [100]))
        product = self.queryset.get()
        self.assertListEqual(obj.coordinates, [[0, 15, 25], [15, 35, 40, 100], [45, 60, 90]])