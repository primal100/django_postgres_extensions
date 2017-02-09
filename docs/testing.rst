Running Tests
=============

Running
-------

To run the tests

``$ git clone https://github.com/primal100/django_postgres_extensions.git dpe_repo``

``$ cd dpe-repo/tests``

``$ ./runtests.py --exclude-tag=benchmark``

Benchmarks
----------

Benchmark tests are included to compare performance of the Array M2M with the traditional Django table-based M2M.
They can be quite slow and thus it is recommended to exclude them when running tests altogether as in the above example.

They can be run with:

``$ ./runtests.py benchmarks.tests``