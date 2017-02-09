from __future__ import unicode_literals

from django.test import override_settings
from django.contrib.auth import get_user_model
from django.contrib.admin.tests import AdminSeleniumTestCase
from selenium.common.exceptions import NoSuchWindowException
from .models import Product, Buyer
import time
import ast

installed_apps = [
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sites',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'django_postgres_extensions',
    'modeladmin'
]

@override_settings(ROOT_URLCONF='modeladmin.urls', INSTALLED_APPS=installed_apps, DEBUG=True)
class PostgresAdminTestCase(AdminSeleniumTestCase):

    close_manually = False

    browsers = ['chrome']

    available_apps = installed_apps

    username = 'super'
    password = 'secret'
    email = 'super@example.com'
    app_name = 'modeladmin'
    model_name = 'product'

    @classmethod
    def setUpClass(cls):
        super(PostgresAdminTestCase, cls).setUpClass()
        cls.selenium.maximize_window()
        cls.url = '%s/%s/%s/%s' % (cls.live_server_url, 'admin', cls.app_name, cls.model_name)

    def tearDown(self):
        time.sleep(3)
        while self.close_manually:
            try:
                self.wait_page_loaded()
            except NoSuchWindowException:
                self.close_manually = False
        super(PostgresAdminTestCase, self).tearDown()

    def setUp(self):
        super(PostgresAdminTestCase, self).setUp()
        User = get_user_model()
        if not User.objects.filter(username=self.username).exists():
            User.objects.create_superuser(username=self.username, password=self.password, email=self.email)
        self.admin_login(self.username, self.password)

    def test_list(self):
        prod = Product(name='Pro Trainers', keywords=['fun', 'popular'],
                       sports=['tennis', 'basketball'],
                       shipping={
                           'Address': 'Pearse Street',
                           'City': 'Dublin',
                           'Region': 'Co. Dublin',
                           'Country': 'Ireland'
                       },
                       details={
                           'brand': {
                               'name': 'Adidas',
                               'country': 'Germany',
                           },
                           'type': 'runners',
                           'colours': ['black', 'white', 'blue']
                       }
                       )

        prod.save()
        self.selenium.get(self.url)
        self.wait_page_loaded()
        element = self.selenium.find_elements_by_class_name('field-name')[0]
        self.assertEqual(element.text, "Pro Trainers")
        element = self.selenium.find_elements_by_class_name('field-keywords')[0]
        self.assertEqual(element.text, 'fun, popular')
        element = self.selenium.find_elements_by_class_name('field-shipping')[0]
        self.assertDictEqual(ast.literal_eval(element.text), {'City': 'Dublin', 'Region': 'Co. Dublin', 'Country': 'Ireland', 'Address': 'Pearse Street'})
        element = self.selenium.find_elements_by_class_name('field-details')[0]
        self.assertDictEqual(ast.literal_eval(element.text), {'colours': ['black', 'white', 'blue'], 'brand': {'country': 'Germany', 'name': 'Adidas'}, 'type': 'runners'})
        element = self.selenium.find_elements_by_class_name('field-country')[0]
        self.assertEqual(element.text, "Ireland")

    def fill_form(self, ids_values, select_values, many_to_many_select, replace=False):
        for id, value in ids_values:
            element = self.selenium.find_element_by_id(id)
            if replace:
                element.clear()
            element.send_keys(value)
        for select in select_values:
            selector, values = select
            for value in values:
                selection_box = "#id_%s" % selector
                self.get_select_option(selection_box, value).click()
        for field_name, values in many_to_many_select:
            from_box = '#id_%s_from' % field_name
            choose_link = 'id_%s_add_link' % field_name
            choose_elem = self.selenium.find_element_by_id(choose_link)
            for value in values:
                self.get_select_option(from_box, str(value)).click()
                choose_elem.click()
        self.selenium.find_element_by_xpath('//input[@value="Save"]').click()
        self.wait_page_loaded()

    def test_add(self):
        buyer1 = Buyer(name='Muhammed Ali')
        buyer1.save()
        buyer2 = Buyer(name='Conor McGregor')
        buyer2.save()
        buyer3 = Buyer(name='Floyd Mayweather')
        buyer3.save()
        self.selenium.get('%s/%s' % (self.url, 'add'))
        self.wait_page_loaded()
        ids_values = (("id_name", "Pro Trainers"), ("id_keywords_0", "fun"), ("id_keywords_1", "popular"),
                      ("id_shipping_address", "Pearse Street"), ("id_shipping_city", "Dublin"), ("id_shipping_region", "Co.Dublin"),
                      ("id_shipping_country", "Ireland"), ("id_details_brand_name", "Adidas"), ("id_details_brand_country", "Germany"),
                      ("id_details_type", "Runners"), ("id_details_colours_0", "Black"), ("id_details_colours_1", "White"),
                      ("id_details_colours_2", "Blue"))
        select_values = (("sports", ("tennis", "basketball"),),)
        many_to_many_select = (("buyers", (buyer1.pk, buyer3.pk),),)
        self.fill_form(ids_values, select_values, many_to_many_select)
        obj = Product.objects.get()
        self.assertEqual(obj.name, 'Pro Trainers')
        self.assertDictEqual(obj.shipping, {'City': 'Dublin', 'Region': 'Co.Dublin', 'Country': 'Ireland',
                                           'Address': 'Pearse Street'})
        self.assertListEqual(obj.sports, ['tennis', 'basketball'])
        self.assertListEqual(obj.details['Colours'], ['Black', 'White', 'Blue', '', '', '', '', '', '', ''])
        self.assertDictEqual(obj.details['Brand'], {'Country': 'Germany', 'Name': 'Adidas'})
        self.assertEqual(obj.details['Type'], 'Runners')
        self.assertListEqual(obj.keywords,['fun', 'popular'])
        buyers = obj.buyers.all().order_by('id')
        self.assertQuerysetEqual(buyers, ['<Buyer: Muhammed Ali>', '<Buyer: Floyd Mayweather>'])

    def test_update(self):
        buyer1 = Buyer(name='Muhammed Ali')
        buyer1.save()
        buyer2 = Buyer(name='Conor McGregor')
        buyer2.save()
        buyer3 = Buyer(name='Floyd Mayweather')
        buyer3.save()
        prod = Product(name='Pro Trainers', keywords=['fun', 'popular'],
                       sports=['tennis', 'basketball'],
                       shipping={
                           'Address': 'Pearse Street',
                           'City': 'Dublin',
                           'Region': 'Co. Dublin',
                           'Country': 'Ireland'
                       },
                       details={
                           'Brand': {
                               'Name': 'Adidas',
                               'Country': 'Germany',
                           },
                           'Type': 'runners',
                           'Colours': ['black', 'white', 'blue']
                       }
                       )

        prod.save()
        prod.buyers.add(buyer1, buyer3)
        self.selenium.get('%s/%s/%s' % (self.url, prod.pk, 'change'))
        self.wait_page_loaded()
        ids_values = (("id_keywords_1", "not popular"),
                      ("id_shipping_address", "Nassau Street"), ("id_details_brand_name", "Nike"), ("id_details_brand_country", "USA"),
                      ("id_details_colours_3", "Red"))
        select_values = (("sports", ("football",),),)
        many_to_many_select = (("buyers", (buyer2.pk, ),),)
        self.fill_form(ids_values, select_values, many_to_many_select, replace=True)
        obj = Product.objects.get()
        buyers = obj.buyers.all().order_by('id')
        self.assertQuerysetEqual(buyers, ['<Buyer: Muhammed Ali>', '<Buyer: Conor McGregor>', '<Buyer: Floyd Mayweather>'])
        self.assertEqual(obj.name, 'Pro Trainers')
        self.assertDictEqual(obj.shipping, {'City': 'Dublin', 'Region': 'Co. Dublin', 'Country': 'Ireland',
                                           'Address': 'Nassau Street'})
        self.assertListEqual(obj.sports, ['football', 'tennis', 'basketball'])
        self.assertListEqual(obj.details['Colours'], ['black', 'white', 'blue', 'Red', '', '', '', '', '', ''])
        self.assertDictEqual(obj.details['Brand'], {'Country': 'USA', 'Name': 'Nike'})
        self.assertEqual(obj.details['Type'], 'runners')
        self.assertListEqual(obj.keywords,['fun', 'not popular'])

    def test_delete(self):
        buyer1 = Buyer(name='Muhammed Ali')
        buyer1.save()
        buyer2 = Buyer(name='Conor McGregor')
        buyer2.save()
        buyer3 = Buyer(name='Floyd Mayweather')
        buyer3.save()
        prod = Product(name='Pro Trainers', keywords=['fun', 'popular'],
                       sports=['tennis', 'basketball'],
                       shipping={
                           'Address': 'Pearse Street',
                           'City': 'Dublin',
                           'Region': 'Co. Dublin',
                           'Country': 'Ireland'
                       },
                       details={
                           'Brand': {
                               'Name': 'Adidas',
                               'Country': 'Germany',
                           },
                           'Type': 'runners',
                           'Colours': ['black', 'white', 'blue']
                       }
                       )

        prod.save()
        prod.buyers.add(buyer1, buyer3)
        self.selenium.get('%s/%s/%s' % (self.url, prod.pk, 'delete'))
        self.selenium.find_element_by_xpath('//input[@value="Yes, I\'m sure"]').click()
        self.assertEqual(Product.objects.count(), 0)