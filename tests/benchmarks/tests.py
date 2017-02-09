from __future__ import unicode_literals
from django.test import TestCase
from django.db import connections
from django.test import tag
import time
from django_postgres_extensions.models.functions import ArrayAppend, ArrayCat
from .models import Traditional, NumberArray, NumberTraditional, Array

@tag('benchmark')
class BaseBenchmark(TestCase):
    def checkTimes(self, text, func1, func2, args1=(), kwargs1=None, args2=(), kwargs2=None, verify_result=None,
                   first="Traditional M2M", second="Array M2M"):
        start = time.clock()
        kwargs = kwargs1 or {}
        result1= func1(*args1, **kwargs)
        traditional_time = time.clock() - start
        start = time.clock()
        kwargs = kwargs2 or {}
        result2 = func2(*args2, **kwargs)
        array_time = time.clock() - start
        if verify_result:
            verify_result(result1, result2)
        times = "%s: %s. %s: %s" % (first, traditional_time, second, array_time)
        if traditional_time > array_time:
            print("Test %s: %s is faster. %s" % (text, second, times))
        elif traditional_time < array_time:
            print("Test %s: %s is faster. %s" % (text, first, times))
        else:
            print("Test %s: Times are equal. %s" % (text, times))

@tag('benchmark')
class ArrayBenchmarks(BaseBenchmark):

    @classmethod
    def setUpTestData(cls):
        cls.array = Array(index=3)
        cls.array.save()
        numbers_array = []
        for i in range(0, 100):
            numberarray = NumberArray(index=i)
            numbers_array.append(numberarray)
        numbers_array = NumberArray.objects.bulk_create(numbers_array)
        cls.numbers_array = [x.pk for x in numbers_array]
        cls.array.numbers.add(*cls.numbers_array)
        cls.numbers_array = numbers_array

    def test_append_cat_one(self):
        numberarray = NumberArray(index=101)
        numberarray.save()
        kwargs1 = {'numbers': ArrayAppend('numbers_ids', numberarray.pk)}
        kwargs2 = {'numbers': ArrayCat('numbers_ids', [numberarray.pk])}
        self.checkTimes('Append vs Cat', Array.objects.update, Array.objects.update, kwargs1=kwargs1,
                        kwargs2=kwargs2, first="Append", second="Cat")

@tag('benchmark')
class ForwardWriteBenchmarks(BaseBenchmark):

    @classmethod
    def setUpTestData(cls):
        cls.traditional = Traditional(index=2)
        cls.traditional.save()
        cls.array = Array(index=3)
        cls.array.save()

    def test_add_1(self):
        numbers_trad, numbers_array = self.create_objs(2)
        number_trad1 = numbers_trad[0]
        number_trad2 = numbers_trad[1]
        number_array1 = numbers_array[0]
        number_array2 = numbers_array[1]
        self.checkTimes('Add 1 New', self.traditional.numbers.add, self.array.numbers.add, args1=(number_trad1,),
                        args2=(number_array1,))
        self.checkTimes('Add 1 Existing', self.traditional.numbers.add, self.array.numbers.add, args1=(number_trad2,),
                        args2=(number_array2,))

    def test_add_10(self):
        numbers_trad, numbers_array = self.create_objs(20, add=False)
        numbers_trad1 = numbers_trad[0:10]
        numbers_trad2 = numbers_trad[11:20]
        numbers_array1 = numbers_array[0:10]
        numbers_array2 = numbers_array[11:20]
        self.checkTimes('Add 10 New', self.traditional.numbers.add, self.array.numbers.add, args1=numbers_trad1,
                        args2=numbers_array1)
        self.checkTimes('Add 10 Existing', self.traditional.numbers.add, self.array.numbers.add, args1=numbers_trad2,
                        args2=numbers_array2)

    def test_add_10000(self):
        numbers_trad, numbers_array = self.create_objs(20000, add=False)
        numbers_trad1 = numbers_trad[0:10000]
        numbers_trad2 = numbers_trad[10001:20000]
        numbers_array1 = numbers_array[0:10000]
        numbers_array2 = numbers_array[10001:20000]
        self.checkTimes('Add 10000 New', self.traditional.numbers.add, self.array.numbers.add, args1=numbers_trad1,
                        args2=numbers_array1)
        self.checkTimes('Add 10000 Existing', self.traditional.numbers.add, self.array.numbers.add, args1=numbers_trad2,
                        args2=numbers_array2)

    def test_remove_1(self):
        numbers_trad, numbers_array = self.create_objs(2)
        number_trad1 = numbers_trad[0]
        number_trad2 = numbers_trad[1]
        number_array1 = numbers_array[0]
        number_array2 = numbers_array[1]
        self.checkTimes('Remove 1 Partial', self.traditional.numbers.remove, self.array.numbers.remove, args1=(number_trad1,),
                        args2=(number_array1,))
        self.checkTimes('Remove 1 Remaining', self.traditional.numbers.remove, self.array.numbers.remove,
                        args1=(number_trad2,), args2=(number_array2,))


    def test_remove_10(self):
        numbers_trad, numbers_array = self.create_objs(20)
        numbers_trad1 = numbers_trad[0:10]
        numbers_trad2 = numbers_trad[11:20]
        numbers_array1 = numbers_array[0:10]
        numbers_array2 = numbers_array[11:20]
        self.checkTimes('Remove 10 partial', self.traditional.numbers.remove, self.array.numbers.remove, args1=numbers_trad1,
                        args2=numbers_array1)
        self.checkTimes('Remove 10 all', self.traditional.numbers.remove, self.array.numbers.remove, args1=numbers_trad2,
                        args2=numbers_array2)

    def test_remove_10000(self):
        numbers_trad, numbers_array = self.create_objs(20000)
        numbers_trad1 = numbers_trad[0:10000]
        numbers_trad2 = numbers_trad[10001:20000]
        numbers_array1 = numbers_array[0:10000]
        numbers_array2 = numbers_array[10001:20000]
        self.checkTimes('Remove 10000 Partial', self.traditional.numbers.remove, self.array.numbers.remove, args1=numbers_trad1,
                        args2=numbers_array1)
        self.checkTimes('Remove 10000 All', self.traditional.numbers.remove, self.array.numbers.remove,
                        args1=numbers_trad2,
                        args2=numbers_array2)

    def test_clear_10(self):
        self.create_objs(10)
        self.assertEqual(self.traditional.numbers.count(), 10)
        self.assertEqual(self.array.numbers.count(), 10)
        self.checkTimes('Clear 10000', self.traditional.numbers.clear, self.array.numbers.clear)
        self.assertEqual(self.traditional.numbers.count(), 0)
        self.assertEqual(self.array.numbers.count(), 0)

    def create_objs(self, number, add=True):
        numbers_trad = []
        numbers_array = []
        for i in range(0, number):
            numbertrad = NumberTraditional(index=i)
            numbers_trad.append(numbertrad)
            numberarray = NumberArray(index=i)
            numbers_array.append(numberarray)
        numbers_trad = NumberTraditional.objects.bulk_create(numbers_trad)
        numbers_trad = [x.pk for x in numbers_trad]
        numbers_array = NumberArray.objects.bulk_create(numbers_array)
        numbers_array = [x.pk for x in numbers_array]
        if add:
            self.traditional.numbers.add(*numbers_trad)
            self.array.numbers.add(*numbers_array)
            self.assertEqual(self.traditional.numbers.count(), number)
            self.assertEqual(self.array.numbers.count(), number)
        return numbers_trad, numbers_array

    def test_clear_10000(self):
        self.create_objs(10000)
        self.checkTimes('Clear 10000', self.traditional.numbers.clear, self.array.numbers.clear)
        self.assertEqual(self.traditional.numbers.count(), 0)
        self.assertEqual(self.array.numbers.count(), 0)

@tag('benchmark')
class ReverseWriteBenchmarks(BaseBenchmark):

    @classmethod
    def setUpTestData(cls):
        cls.numtraditional = NumberTraditional(index=2)
        cls.numtraditional.save()
        cls.numarray = NumberArray(index=3)
        cls.numarray.save()

    def test_add_1(self):
        trads, arrays = self.create_objs(2, add=False)
        trad1 = trads[0]
        trad2 = trads[1]
        array1 = arrays[0]
        array2 = arrays[1]
        self.checkTimes('Add 1 New', self.numtraditional.traditional_set.add, self.numarray.array_set.add, args1=(trad1,),
                        args2=(array1,))
        self.checkTimes('Add 1 Existing', self.numtraditional.traditional_set.add, self.numarray.array_set.add, args1=(trad2,),
                        args2=(array2,))

    def test_add_10(self):
        trads, arrays = self.create_objs(20, add=False)
        trad1 = trads[0:10]
        trad2 = trads[11:20]
        array1 = arrays[0:10]
        array2 = arrays[11:20]
        self.checkTimes('Add 10 New', self.numtraditional.traditional_set.add, self.numarray.array_set.add, args1=trad1,
                        args2=array1)
        self.checkTimes('Add 10 Existing', self.numtraditional.traditional_set.add, self.numarray.array_set.add, args1=trad2,
                        args2=array2)

    def test_add_1000(self):
        trads, arrays = self.create_objs(2000, add=False)
        trad1 = trads[0:1000]
        trad2 = trads[1001:2000]
        array1 = arrays[0:1000]
        array2 = arrays[1001:2000]
        self.checkTimes('Add 1000 New', self.numtraditional.traditional_set.add, self.numarray.array_set.add, args1=trad1,
                        args2=array1)
        self.checkTimes('Add 1000 Existing', self.numtraditional.traditional_set.add, self.numarray.array_set.add,
                    args1=trad2, args2=array2)


    def test_remove_1(self):
        numbers_trad, numbers_array = self.create_objs(2)
        number_trad1 = numbers_trad[0]
        number_trad2 = numbers_trad[1]
        number_array1 = numbers_array[0]
        number_array2 = numbers_array[1]
        self.checkTimes('Remove 1 Partial', self.numtraditional.traditional_set.remove, self.numarray.array_set.remove,
                        args1=(number_trad1,), args2=(number_array1,))
        self.checkTimes('Remove 1 Remaining', self.numtraditional.traditional_set.remove, self.numarray.array_set.remove,
                        args1=(number_trad2,), args2=(number_array2,))


    def test_remove_10(self):
        numbers_trad, numbers_array = self.create_objs(20)
        number_trad1 = numbers_trad[0:10]
        number_trad2 = numbers_trad[10:20]
        number_array1 = numbers_array[0:10]
        number_array2 = numbers_array[10:20]
        self.checkTimes('Remove 10 Partial', self.numtraditional.traditional_set.remove, self.numarray.array_set.remove,
                        args1=number_trad1, args2=number_array1)
        self.checkTimes('Remove 10 Remaining', self.numtraditional.traditional_set.remove, self.numarray.array_set.remove,
                        args1=number_trad2, args2=number_array2)

    def test_remove_1000(self):
        numbers_trad, numbers_array = self.create_objs(2000)
        number_trad1 = numbers_trad[0:1000]
        number_trad2 = numbers_trad[1000:2000]
        number_array1 = numbers_array[0:1000]
        number_array2 = numbers_array[1000:2000]
        self.checkTimes('Remove 1000 Partial', self.numtraditional.traditional_set.remove, self.numarray.array_set.remove,
                        args1=number_trad1, args2=number_array1)
        self.checkTimes('Remove 1000 Remaining', self.numtraditional.traditional_set.remove, self.numarray.array_set.remove,
                        args1=number_trad2, args2=number_array2)

    def test_clear_10(self):
        self.create_objs(10)
        self.assertEqual(self.numtraditional.traditional_set.count(), 10)
        self.assertEqual(self.numarray.array_set.count(), 10)
        self.checkTimes('Clear 10', self.numtraditional.traditional_set.clear, self.numarray.array_set.clear)
        self.assertEqual(self.numtraditional.traditional_set.count(), 0)
        self.assertEqual(self.numarray.array_set.count(), 0)

    def test_clear_1000(self):
        self.create_objs(1000)
        self.assertEqual(self.numtraditional.traditional_set.count(), 1000)
        self.assertEqual(self.numarray.array_set.count(), 1000)
        self.checkTimes('Clear 1000', self.numtraditional.traditional_set.clear, self.numarray.array_set.clear)
        self.assertEqual(self.numtraditional.traditional_set.count(), 0)
        self.assertEqual(self.numarray.array_set.count(), 0)

    def create_objs(self, number, add=True):
        trads = []
        arrays = []
        for i in range(0, number):
            trad = Traditional(index=i)
            trads.append(trad)
            array = Array(index=i)
            arrays.append(array)
        trads = Traditional.objects.bulk_create(trads)
        trads = [x.pk for x in trads]
        arrays = Array.objects.bulk_create(arrays)
        arrays = [x.pk for x in arrays]
        if add:
            self.numtraditional.traditional_set.add(*trads)
            self.numarray.array_set.add(*arrays)
            self.assertEqual(self.numtraditional.traditional_set.count(), number)
            self.assertEqual(self.numarray.array_set.count(), number)
        return trads, arrays

@tag('benchmark')
class ReadBenchmarks(BaseBenchmark):

    @classmethod
    def setUpTestData(cls):
        cls.connection = connections['default']
        numtrads, numarrays = [], []
        for i in range(0, 200):
            trad = NumberTraditional(index=i)
            array = NumberArray(index=i)
            numtrads.append(trad)
            numarrays.append(array)
        NumberTraditional.objects.bulk_create(numtrads)
        NumberArray.objects.bulk_create(numarrays)
        numtrads1 = NumberTraditional.objects.all()[0:100]
        numtrads2 = NumberTraditional.objects.all()[100:200]
        cls.numtrad = numtrads2[50]
        numarrays1 = NumberArray.objects.all()[0:100]
        numarrays2 = NumberArray.objects.all()[100:200]
        cls.numarray = numarrays2[50]
        num = 1000
        trads, arrays = [], []
        for i in range(0, num):
            trad = Traditional(index=i)
            array = Array(index=i)
            trads.append(trad)
            arrays.append(array)
        Traditional.objects.bulk_create(trads)
        Array.objects.bulk_create(arrays)
        trads = Traditional.objects.all()
        arrays = Array.objects.all()
        to_add = numtrads1
        for trad in trads:
            trad.numbers.add(*to_add)
            if to_add == numtrads1:
                to_add = numtrads2
            else:
                to_add = numtrads1
        to_add = numarrays1
        for array in arrays:
            array.numbers.add(*to_add)
            if to_add == numarrays1:
                to_add = numarrays2
            else:
                to_add = numarrays1

    def setUp(self):
        super(ReadBenchmarks, self).setUp()
        self.assertEqual(Traditional.objects.count(), 1000)
        self.assertEqual(Array.objects.count(), 1000)

    def test_lookup_id(self):
        qs1 = Traditional.objects.filter(numbers=self.numtrad)
        qs2 = Array.objects.filter(numbers=self.numarray)
        self.assertEqual(qs1.count(),500)
        self.assertEqual(qs2.count(), 500)
        sql, params = qs2._as_sql(self.connection)
        with self.connection.cursor() as cursor:
            cursor.execute("EXPLAIN " + sql, params)
            #print(cursor.fetchall())
        self.checkTimes('forward lookup_id 1000x100', list, list, args1=(qs1,),
                        args2=(qs2,))

    def test_reverse_lookup_id(self):
        trad = Traditional.objects.order_by('id').first()
        array = Array.objects.order_by('id').first()
        qs1 = NumberTraditional.objects.filter(traditional=trad)
        qs2 = NumberArray.objects.filter(array=array)
        self.assertEqual(qs1.count(),100)
        self.assertEqual(qs2.count(), 100)
        sql, params = qs2._as_sql(self.connection)
        with self.connection.cursor() as cursor:
            cursor.execute("EXPLAIN " + sql, params)
            #print(cursor.fetchall())
        self.checkTimes('reverse lookup_id 1000x100', list, list, args1=(qs1,),
                        args2=(qs2,))

    def test_reverse_lookup_other_field(self):
        qs1 = NumberTraditional.objects.filter(traditional__index=15)
        qs2 = NumberArray.objects.filter(array__index=15)
        self.assertEqual(qs1.count(),100)
        self.assertEqual(qs2.count(), 100)
        sql, params = qs2._as_sql(self.connection)
        with self.connection.cursor() as cursor:
            cursor.execute("EXPLAIN " + sql, params)
        self.checkTimes('reverse lookup other field 1000x100', list, list, args1=(qs1,),
                        args2=(qs2,))

    def test_lookup_other_field(self):
        qs1 = Traditional.objects.filter(numbers__index=80)
        qs2 = Array.objects.filter(numbers__index=80)
        self.assertEqual(qs1.count(),500)
        self.assertEqual(qs2.count(), 500)
        self.checkTimes('forward lookup other field 1000x100', list, list, args1=(qs1,),
                        args2=(qs2,))

    def test_forward_descriptor_all(self):
        trad = Traditional.objects.order_by('id').first()
        array = Array.objects.order_by('id').first()
        qs1 = trad.numbers.all()
        qs2 = array.numbers.all()
        self.assertEqual(qs1.count(), qs2.count())
        self.checkTimes('Forward descriptor all()', list, list, args1=(qs1,), args2=(qs2,))

    def test_reverse_descriptor_all(self):
        tradnum = NumberTraditional.objects.order_by('id').first()
        arraynum = NumberArray.objects.order_by('id').first()
        qs1 = tradnum.traditional_set.all()
        qs2 = arraynum.array_set.all()
        self.assertEqual(qs1.count(), qs2.count())
        self.checkTimes('Reverse descriptor all()', list, list, args1=(qs1,), args2=(qs2,))

@tag('benchmark')
class ModelSavingBenchmarks(BaseBenchmark):

    @classmethod
    def setUpTestData(cls):
        cls.numtraditional = NumberTraditional(index=2)
        cls.numtraditional.save()
        cls.numarray = NumberArray(index=3)
        cls.numarray.save()

    def create_for_traditional(self, num):
        traditionals = []
        for i in range(0, num):
            trad = Traditional(index=i)
            traditionals.append(trad)
        Traditional.objects.bulk_create(traditionals)
        self.assertEqual(Traditional.objects.all().count(), num)
        for i in range(0, num):
            trad = Traditional.objects.get(index=i)
            trad.numbers.add(self.numtraditional)
        return traditionals

    def create_for_array(self, num):
        arrays = []
        for i in range(0, num):
            arr = Array(index=i, numbers_ids=[self.numarray.pk])
            arrays.append(arr)
        Array.objects.bulk_create(arrays)
        return arrays

    def test_create(self):
        self.checkTimes('Create 1', self.create_for_traditional, self.create_for_array,
                        args1=(1,), args2=(1,))
        Traditional.objects.all().delete()
        self.checkTimes('Create 10', self.create_for_traditional, self.create_for_array,
                        args1=(10,), args2=(10,))
        Traditional.objects.all().delete()
        self.checkTimes('Create 1000', self.create_for_traditional, self.create_for_array,
                        args1=(1000,), args2=(10,))
        Traditional.objects.all().delete()

    def test_delete(self):
        trad = self.create_for_traditional(1)[0]
        arr = self.create_for_array(1)[0]
        self.checkTimes('Delete 1', trad.delete, arr.delete)
        self.create_for_traditional(10)
        self.create_for_array(10)
        self.checkTimes('Delete 10', Traditional.objects.all().delete, Array.objects.all().delete)
        self.create_for_traditional(1000)
        self.create_for_array(1000)
        self.checkTimes('Delete 10000', Traditional.objects.all().delete, Array.objects.all().delete)

