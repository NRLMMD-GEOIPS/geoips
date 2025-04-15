.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

🖍️ Coding Standards Reference Doc
=================================

*"Although that way may not be obvious at first unless you're Dutch."*
- the Zen of Python

.. contents::

Summary
-------

The goal is consistency. In style, we're in the right even if we're all wrong together.
GeoIPS code is meant to be re-used by many, and we expect that the code will be read
much more than it is written. The goal of this document is to help us spend less time
on conventions and more time making GeoIPS better.

We use - in order of supremacy - a few Internal Standards, followed by the numpy
docstring standards and the python style guide laid out in PEP 8.

bandit, flake8, and black are used to enforce appropriate style, security,
and syntax usage.  flake8-rst and flake8-rst-docstring plugins are used to
enforce numpy docstring formatting.  Sphinx is used to validate the
formatting and syntax within RST files themselves.

Corresponding configuration files for both black and flake8 can be found
in the geoips directory ``.config/``.

All branches must pass the ``geoips/tests/utils/check_code.sh`` script
prior to any Pull Requests being approved and merged.  Please ensure this
script has a successful 0 return as you develop code within the GeoIPS
Ecosystem to expedite the review and approval process.

This document will detail internal standard conventions and include some of the external
standards for easy reference. For external standards, the primary source is always
right in the case of a conflict with this document.

External Style Standards
------------------------

Numpy Docstrings
^^^^^^^^^^^^^^^^

Full information here: `Docstring Standard <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_

Common mishaps:
"""""""""""""""

The first docstring line should be a "one-line summary that **does not use variable
names or the function name**"

Classes
"""""""

.. dropdown:: Example

  .. code-block:: python

    class Calculator:
        """A simple calculator class for performing basic arithmetic operations.

        This class provides methods to add, subtract, multiply, and divide
        two numeric values. It also includes a `safe_divide` method to handle
        division by zero more gracefully.

        .. deprecated:: 1.1.0
          The `divide` method will be removed in version 2.0.0.
          Use `safe_divide` instead, which handles division by zero.

        Extended Summary
        ----------------
        The `Calculator` class is designed for basic arithmetic operations
        such as addition, subtraction, multiplication, and division. It is
        useful for simple computational tasks and educational purposes.

        The `safe_divide` method is a safer version of `divide` that returns
        `inf` when dividing by zero, rather than raising an error.

        Parameters
        ----------
        log_operations : bool, optional
            If True, all operations will be logged to a file (default is False).

        Attributes
        ----------
        log_operations : bool
            Indicates whether operations will be logged to a file.

        Other Parameters
        ----------------
        output_format : str, optional
            Format for the output of arithmetic operations. It must be one of
            `{'decimal', 'fraction'}`. Default is 'decimal'.

        Raises
        ------
        ZeroDivisionError
            If `divide` is used with the second operand as zero.

        See Also
        --------
        numpy.add : Element-wise addition for numpy arrays.
        numpy.subtract : Element-wise subtraction for numpy arrays.
        numpy.multiply : Element-wise multiplication for numpy arrays.

        Notes
        -----
        This class is intended for scalar arithmetic operations. If you are
        working with arrays, you should consider using `numpy` for vectorized
        operations, which will be more efficient.

        References
        ----------
        .. [1] Python Documentation: https://docs.python.org/3/library/operator.html
        .. [2] NumPy Documentation: https://numpy.org/doc/stable/reference/routines.math.html

        Examples
        --------
        Create a `Calculator` object and perform arithmetic operations:

        >>> calc = Calculator()
        >>> calc.add(10, 5)
        15
        >>> calc.subtract(10, 5)
        5
        >>> calc.multiply(10, 5)
        50
        >>> calc.divide(10, 5)
        2.0
        >>> calc.safe_divide(10, 0)
        inf

        """

Sections:

#. `Short summary <https://numpydoc.readthedocs.io/en/latest/format.html#short-summary>`_
#. `Deprecation warning (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#deprecation-warning>`_
#. `Extended Summary <https://numpydoc.readthedocs.io/en/latest/format.html#extended-summary>`_
#. `Parameters (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#parameters>`_
#. `Other Parameters (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#other-parameters>`_
#. `Raises (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#raises>`_
#. `See Also (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#see-also>`_
#. `Notes (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#notes>`_
#. `References (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#references>`_
#. `Examples <https://numpydoc.readthedocs.io/en/latest/format.html#examples>`_

Methods
"""""""

.. dropdown:: Example

  .. code-block:: python

    def matrix_multiply(a, b, out=None):
      """Multiply two matrices.

      Computes the matrix product of two arrays `a` and `b`. If an output array
      is provided, the result is stored in `out`. This function follows the
      standard rules for matrix multiplication in linear algebra.

      .. deprecated:: 1.5.0
        This function will be removed in NumPy 2.0.0.
        Use `numpy.matmul` or `numpy.dot` instead.

      Parameters
      ----------
      a : array_like
          The first matrix to be multiplied.
      b : array_like
          The second matrix to be multiplied.
      out : ndarray, optional
          If provided, the result will be stored in this array. It must have
          the correct shape to store the result.

      Other Parameters
      ----------------
      dtype : data-type, optional
          If specified, forces the operation to cast the inputs to the given
          type before performing the operation.

      Returns
      -------
      output : ndarray
          The matrix product of `a` and `b`. If `out` is provided, this array
          is returned.

      Raises
      ------
      ValueError
          If the shapes of `a` and `b` are not aligned for matrix multiplication.

      See Also
      --------
      numpy.matmul : Matrix product of two arrays.
      numpy.dot : Dot product of two arrays.
      numpy.einsum : Einstein summation convention.

      Notes
      -----
      This function implements the matrix product as described in linear algebra.
      It is different from element-wise multiplication of arrays.

      If either of the inputs is a scalar, it will be broadcast according to
      standard broadcasting rules.

      References
      ----------
      .. [1] Strang, G., "Introduction to Linear Algebra, 5th Edition," Wellesley-Cambridge Press, 2016.

      Examples
      --------
      Multiply two 2x2 matrices:

      >>> import numpy as np
      >>> a = np.array([[1, 2], [3, 4]])
      >>> b = np.array([[5, 6], [7, 8]])
      >>> matrix_multiply(a, b)
      array([[19, 22],
            [43, 50]])

      Store result in a pre-allocated output array:

      >>> out = np.empty((2, 2))
      >>> matrix_multiply(a, b, out=out)
      array([[19, 22],
            [43, 50]])
      >>> out
      array([[19., 22.],
            [43., 50.]])

      """
      import numpy as np

      a = np.asarray(a)
      b = np.asarray(b)

      if out is None:
          return np.dot(a, b)
      else:
          np.dot(a, b, out=out)
          return out


Sections:

#. `Short summary <https://numpydoc.readthedocs.io/en/latest/format.html#short-summary>`_
#. `Deprecation warning (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#deprecation-warning>`_
#. `Extended Summary <https://numpydoc.readthedocs.io/en/latest/format.html#extended-summary>`_
#. `Parameters (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#parameters>`_
#. `Other Parameters (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#other-parameters>`_
#. `Raises (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#raises>`_
#. `See Also (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#see-also>`_
#. `Notes (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#notes>`_
#. `References (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#references>`_
#. `Examples <https://numpydoc.readthedocs.io/en/latest/format.html#examples>`_

More sections necessary for generators/etc. please see the original numpy standards 😄

Modules
"""""""

.. dropdown:: Example

  .. code-block:: python

        """A simple mathematics module for common operations.

        This module provides basic mathematical operations such as addition, subtraction,
        multiplication, and division. It is designed to serve as a utility for quick calculations
        without external dependencies.

        Extended Summary
        ----------------
        The `mymathlib` module is created for educational purposes and provides a minimalistic
        implementation of basic arithmetic operations. Each function performs a specific mathematical
        task and can handle a wide range of input types, including integers and floats. This module
        is intentionally simple to demonstrate NumPy-style documentation and function listings.

        Routine Listings
        ----------------
        add(a, b)
            Return the sum of `a` and `b`.

        subtract(a, b)
            Return the result of `a` minus `b`.

        multiply(a, b)
            Return the product of `a` and `b`.

        divide(a, b)
            Return the result of `a` divided by `b`.

        See Also
        --------
        numpy.add : Adds two arrays element-wise.
        numpy.subtract : Subtracts one array from another element-wise.
        numpy.multiply : Multiplies two arrays element-wise.
        numpy.divide : Divides two arrays element-wise.

        Notes
        -----
        This module does not handle complex numbers or provide error handling for division
        by zero. It assumes valid inputs (integers or floats) for all functions.

        References
        ----------
        .. [1] NumPy documentation, https://numpy.org/doc/stable/reference/routines.math.html
        .. [2] Python official documentation, https://docs.python.org/3/library/math.html

        Examples
        --------
        >>> from mymathlib import add, subtract, multiply, divide
        >>> add(2, 3)
        5
        >>> subtract(10, 5)
        5
        >>> multiply(4, 3)
        12
        >>> divide(9, 3)
        3.0
        """


Sections:

#. `Short summary <https://numpydoc.readthedocs.io/en/latest/format.html#short-summary>`_
#. `Extended summary (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#extended-summary>`_
#. `Routine listings (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#routine-listings>`_
#. `See also (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#see-also>`_
#. `Notes (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#notes>`_
#. `References (optional) <https://numpydoc.readthedocs.io/en/latest/format.html#references>`_
#. `Examples <https://numpydoc.readthedocs.io/en/latest/format.html#examples>`_

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
------------------------

Bring code to standard in a dedicated PR
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We want to separate formatting/standardizing and functional changes to the code so
reviewing code is less painful. Please, if you're improving the functionality of code
and need to bring it to standard:

1. Make a new branch (branch1)
2. Bring the code to standard
3. Open a PR and make a new branch from branch1 (branch2)
4. Make improvements to the functionality of the code on branch 2
5. Open a second PR for branch 2

If easier, you can make the improvement before bringing the code to standard.

If you touch code, it should meet standards
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We strongly recommend you update any functions you work on
if they do not meet the standard. At CIRA, this is a requirement for
PRs to be merged. For others, it's just a strong recommendation -
however, we don't want the burden of updating code to prevent you from contributing.
Please don't spend hours updating a 100,000 line module because you fixed a typo.
use discretion on when updates are needed.

A good rule of thumb is that if you edit something and it doesn't have a docstring,
add it. If you edit more than 20% of a function/class/module, please edit the rest.

Imports shouldn't be buried without a reason
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If an import needs to be buried for efficiency reasons or namespace conflicts,
this should be documented in the docstrings.

Linting/Formatting
==================

The GeoIPS project makes use of several linting tools to help maintain code quality. The
full suite of linters can be installed by installing the "test" dependencies via pip.
For example, if you installed GeoIPS using `pip install .` the linters can be installed
using `pip install .[test]` the following tools to ensure code quality:

Black
-----

We use the `Black formatter <https://github.com/psf/black>`_ with its default
settings. As stated in the Black documentation, it is an uncompromising code
formatter, but it has resulted in significantly more readable code. Applying it
automatically while writing code has also reduced development time since
developers don't need to think about formatting.

Flake8
------

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

.. code-block::

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
