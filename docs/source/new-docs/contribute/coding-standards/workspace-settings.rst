:orphan:

Workspace Settings
===================

Across the programming languages, a high-quality codebase many peers would easily agree upon would have: \

1. code computes as expected
2. code is tested
3. code is documented and readable


We will focus on workspace settings and developer tools which should be in every developer's arsenal to ensure high quality pythonic code to meet the third goal from the list.

In the practical setting, style guides generally help us to write consistent code ensuring that our codebase is highly readable, maintainable, & extensible. `PEP8 <https://peps.python.org/pep-0008/>`_ provides
most of these coding standards and conventions to follow by any Python developer but how do we ensure that you or your fellow developer has met these standards across your work.  \


That's where the two category of tools come into picture:

Linters
=======

Linters scan your code for any syntactic inconsistencies such as invalid indentation. The linters we are going to use in GeoIPS are


We use the `Flake8 linter <https://flake8.pycqa.org/en/latest/>`_ which wraps three other linters namely, *PyFlakes*, *PyCodestyle*, and *ed Batchelder's McCabe script* to enforce `PEP8 <https://peps.python.org/pep-0008/>`_ code standards. We also add several plugins to Flake8 to enforce additional
standards for GeoIPS code. Plugins used include:

- `flake8-docstrings <https://github.com/pycqa/flake8-docstrings>`_ is used to enforce
  the numpy docstring standard.
- `flake8-rst-docstrings <https://github.com/peterjc/flake8-rst-docstrings>`_ is
  used to ensure that docstrings are valid reStructuredText.
- `flake8-rst <https://github.com/flake8-docs/flake8-rst>`_ runs flake8 on code
  snippets in reStructuredText files to ensure proper formatting in
  documentation.

We modify the default behavior of flake8 slightly to make it work well with Black,
ignore specific errors, and configure plugins. GeoIPS specific settings for
flake8 include the following:


```toml
[flake8]
max-line-length=88                   # maximum code line length is 88
count=True
ignore=E203,W503,E712                 # specific errors and warnings to ignore
extend-exclude=_version.py,lib,*_docs,geoips_dev_utils
docstring-convention=numpy
rst-roles=class,func,ref
rst-directives=envvar,exception
rst-substitutions=version
statistics=True
per-file-ignores =
  /*/interfaces/__init__.py:F401
```

**Few Tips**: \

You can run flake8 against each file or folder

.. code-block:: python

   flake8 path/to/code/to/check.py
   # or
   flake8 path/to/code/



Formatters
==========

Formatters restructures your code to validate against set documentation rules for set code spacing, line length, argument positioning etc. This ensures that code goes easy onto the next reader's eyes (including you, bud) and is consistent across your codebase

GeoIPS mainly uses the `Black formatter <https://github.com/psf/black>`_ with its default
settings. As stated in the Black documentation, it is an uncompromizing code
formatter, but it has resulted in significantly more readable code. Applying it
automatically while writing code has also reduced development time since
developers don't need to think about formatting.

Both the linters and formatters in GeoIPS can be installed using `pip install .[lint]`

The CICD pipelines in GeoIPS over GitHub would prompt you an email message when the relevant tests fail.