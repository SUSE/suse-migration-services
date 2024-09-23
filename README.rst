Distribution Migration System
=============================

.. |GitHub Action Unit Types| image:: https://github.com/SUSE/suse-migration-services/actions/workflows/ci-testing.yml/badge.svg
   :target: https://github.com/SUSE/suse-migration-services/actions
.. |Doc| replace:: `Documentation <https://documentation.suse.com/suse-distribution-migration-system/15/html/distribution-migration-system/index.html>`__

|GitHub Action Unit Types|

**Migrate from one major SUSE version to another with the DMS**

Contents
--------

  * |Doc|
  * Contributing

.. _contributing:

Contributing
============

The Python project uses `tox` to setup a development environment
for the desired Python version.

The following procedure describes how to create such an environment:

1.  Let tox create the virtual environment(s):

    .. code:: bash

       $ tox

2.  Activate the virtual environment

    .. code:: bash

       $ source .tox/3/bin/activate

3.  Install requirements inside the virtual environment:

    .. code:: bash

       $ pip install -U pip setuptools
       $ pip install -r .virtualenv.dev-requirements.txt

4.  Let setuptools create/update your entrypoints

    .. code:: bash

       $ ./setup.py develop

Once the development environment is activated and initialized with
the project required Python modules, you are ready to work.

In order to leave the development mode just call:

.. code:: bash

   $ deactivate

To resume your work, change into your local Git repository and
run `source .tox/3/bin/activate` again. Skip step 3 and 4 as
the requirements are already installed.
