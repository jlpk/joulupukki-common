=================
Joulupukki Common
=================

Joulupukki is a generic system to build and distribute packages from sources.

LICENCE AGPLv3

Installation
============

::

    pip install -r requirements
    python setup.py develop

Testing
=======

You may run all tests with ``tox`` or run the tests with a specific interpreter with ``tox -epy27``.

.. note:: Maybe you need to install tox: ``pip instal tox``

Documentation
=============

You can build the documentation ``tox -edocs``. The HTML documentation will be built in ``docs/build/html``.


Dev Env
=======

::

    virtualenv --system-site-packages env
    source env/bin/activate
    pip install -r requirements.txt
    python setup.py develop
