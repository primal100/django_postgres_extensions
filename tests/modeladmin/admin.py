from django.contrib import admin
from django_postgres_extensions.admin.options import PostgresAdmin
from .models import Product, Buyer

class ProductAdmin(PostgresAdmin):
    filter_horizontal = ('buyers',)
    fields = ('name', 'keywords', 'sports', 'shipping', 'details', 'buyers')
    list_display = ('name', 'keywords', 'shipping', 'details', 'country')

admin.site.register(Buyer)
admin.site.register(Product, ProductAdmin)

