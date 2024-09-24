:orphan:

Linters
=======

Linters scan your code for any syntactic inconsistencies.
Both the linters & formatters in GeoIPS can be installed using:

.. code-block:: bash

  pip install geoips[lint]
  # or
  pip install .[lint] # if installing from a cloned git repo

flake8
------

For GeoIPS and GeoIPS plugins, we use `flake8 <https://flake8.pycqa.org/en/latest/>`_
to enforce `PEP8 <https://peps.python.org/pep-0008/>`_. We also use several flake8 plugins:

- `flake8-docstrings <https://github.com/pycqa/flake8-docstrings>`_ for numpy docstring enforcement
- `flake8-rst-docstrings <https://github.com/peterjc/flake8-rst-docstrings>`_ to enforce valid reStructuredText docstrings
- `flake8-rst <https://github.com/flake8-docs/flake8-rst>`_ to enforce valid formatting in documentation code snippets

This is how we configure flake8:


.. code-block:: 

    [flake8]
    max-line-length = 88
    count = True
    ignore = E203, W503, E712  # specific errors and warnings to ignore
    extend-exclude = _version.py, lib, *_docs, geoips_dev_utils
    docstring-convention = numpy
    rst-roles = class, func, ref
    rst-directives = envvar, exception
    rst-substitutions = version
    statistics = True
    per-file-ignores =
      /*/interfaces/__init__.py:F401

You can run flake8 against each file or folder

.. code-block:: python

   flake8 path/to/code/to/check.py
   # or
   flake8 path/to/code/



Formatters
==========

Formatters restructures the code to validate against set documentation rules.

Black
-----

We use `Black <https://github.com/psf/black>`_ formatter with its default settings. It is an uncompromizing code auto-formatter that standardizes python code.

