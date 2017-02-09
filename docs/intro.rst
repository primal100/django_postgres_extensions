Getting started
===============

.. warning::

    Although it generally should work on other versions, Django Postgres Extensions has been tested with Python 3.6 and Django 1.10.5.

Installation
-------------

Install with ``pip install django_postgres_extensions``

Setup project
-------------

In your settings.py, add 'django.contrib.postgres' and 'django_postgres_extensions' to the list of INSTALLED APPS and configure the database to use the included backend (subclassed from the default Django Postgres backend):

.. literalinclude:: settings.py