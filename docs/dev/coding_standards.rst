=================================
🖍️ Coding Standards Reference Doc
=================================

*"Although that way may not be obvious at first unless you're Dutch."*
- the Zen of Python


.. contents::

Summary
=======

The goal is consistency. In style, we're in the right even if we're all wrong together.
GeoIPS code is meant to be re-used by many, and we expect that the code will be read
much more than it is written. The goal of this document is to help us spend less time
on conventions and more time making GeoIPS better.

We use - in order of supremacy - a few Internal Standards, followed by the numpy
docstring standards and the python style guide laid out in PEP 8.

This document will detail internal standard conventions and include some of the external
standards for easy reference. For external standards, the primary source is always
right in the case of a conflict with this document.

External Style Standards
------------------------

`PEP 8 <https://peps.python.org/pep-0008/>`__
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A nice version of PEP8 can be found at: `PEP8.org <https://pep8.org/>`

Some highlights below for reference.

Function Names
""""""""""""""

Function names should be lowercase, with words separated by
underscores as necessary to improve readability.

`PEP8 Names Standards <https://pep8.org/#naming-conventions>`__

Class Names
"""""""""""

Class names should normally use the CapWords convention.

`PEP8 Names Standards <https://pep8.org/#naming-conventions>`__

Exception Names
"""""""""""""""

Because exceptions should be classes, the class naming convention applies here.
However, you should use the suffix "Error" on your exception names
(if the exception actually is an error).

`PEP8 Names Standards <https://pep8.org/#naming-conventions>`__

Module Names
""""""""""""

Modules should have **short**, **all-lowercase names**.
Underscores can be used in the module name if it improves readability.
`PEP8 Names Standards <https://pep8.org/#naming-conventions>`__

Imports
^^^^^^^
Imports should usually be on separate lines, e.g.:

Yes:

.. code-block:: python

    import os
    import sys

No:

.. code-block:: python

    import os, sys

It's okay to say this though:

.. code-block:: python

    from subprocess import Popen, PIPE

Imports are always put at the top of the file, just after any module comments and
docstrings, and before module globals and constants.

`PEP8 Imports Standards <https://pep8.org/#imports>`__

Internal Style Standards
-------------------------

Imports Shouldn't Be Buried Without a Reason
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If an import needs to be buried for efficiency reasons or namespace conflicts,
this should be documented in the docstrings.


Linting/Formatting
^^^^^^^^^^^^^^^^^^

The GeoIPS project makes use of several linting tools to help maintain code quality. The
full suite of linters can be installed by installing the "test" dependencies via pip.
For example, if you installed GeoIPS using `pip install .` the linters can be installed
using `pip install .[test]` the following tools to ensure code quality:

Black
^^^^^

We use the `Black formatter <https://github.com/psf/black>`_ with its default
settings. As stated in the Black documentation, it is an uncompromizing code
formatter, but it has resulted in significantly more readable code. Applying it
automatically while writing code has also reduced development time since
developers don't need to think about formatting.

Flake8
^^^^^^

We use the `Flake8 linter <https://flake8.pycqa.org/en/latest/>`_ to enforce
PEP8 code standards. We also add several plugins to Flake8 to enforce additional
standards for GeoIPS code. Plugins used include:

- `flake8-docstrings <https://github.com/pycqa/flake8-docstrings>`_ is used to enforce
  the numpy docstring standard.
- `flake8-rst-docstrings <https://github.com/peterjc/flake8-rst-docstrings>`_ is
  used to ensure that docstrings are valid reStructuredText.
- `flake8-rst <https://github.com/flake8-docs/flake8-rst>` runs flake8 on code
  snippets in reStructuredText files to ensure proper formatting in
  documentation.

We modify the default behavior of flake8 slightly to make it work well with Black,
ignore specific errors, and configure plugins. GeoIPS specific settings for
flake8 include the following:

```toml
[flake8]
max-line-length=88
count=True
ignore=E203,W503,E712
extend-exclude=_version.py,lib,*_docs,geoips_dev_utils
docstring-convention=numpy
rst-roles=class,func,ref
rst-directives=envvar,exception
rst-substitutions=version
statistics=True
per-file-ignores =
  /*/interfaces/__init__.py:F401
```

Github Conventions
------------------

Pull Request Workflow
^^^^^^^^^^^^^^^^^^^^^

`https://nrlmmd-geoips.github.io/geoips/devguide/git_workflow.html#geoips-github-pull-request-workflow <https://nrlmmd-geoips.github.io/geoips/devguide/git_workflow.html#geoips-github-pull-request-workflow>`__

`https://nrlmmd-geoips.github.io/geoips/devguide/git_workflow.html#geoips-merge-pr-and-close-issue-workflow <https://nrlmmd-geoips.github.io/geoips/devguide/git_workflow.html#geoips-merge-pr-and-close-issue-workflow>`__

Issue Workflow
^^^^^^^^^^^^^^

`https://nrlmmd-geoips.github.io/geoips/devguide/git_workflow.html#geoips-github-issue-creation-workflow <https://nrlmmd-geoips.github.io/geoips/devguide/git_workflow.html#geoips-github-issue-creation-workflow>`__

Other Conventions
-----------------
