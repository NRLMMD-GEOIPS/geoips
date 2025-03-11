.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Documentation Building
**********************

We use ``Sphinx``, ``pinkrst`` and ``brassy`` to build our documentation.
For more information, see :doc:`./../architecture/documentation/index`.

Documentation can be built by calling ``python3 ./docs/build_docs.py``.

Usage
=====
Run `build_docs.py`  with the required positional arguments and optional flags:

.. code-block:: bash

    python build_docs.py [OPTIONS] <package_name>

**package_name:** Name of the package to build (e.g., geoips, data_fusion).

Optional Arguments
------------------

**--geoips-docs-path:** Path to GeoIPS documentation templates,
used when building geoips plugins.

**--license-url:** URL pointing to the license or distribution statement
for the release notes.
Defaults to ``https://github.com/NRLMMD-GEOIPS/[package_name]``.

**--repo-path:** Path to the repository (e.g., /path/to/geoips).
Defaults to the parent of the directory found by importlib for the provided ``package_name``.
Must be an existing directory and a valid Git repository.

**--output-dir**: Directory where the built documentation will be placed.
Defaults to ``[repo_path]/build/sphinx/html``.

.. warning::

    Some of these optional arguments default to values specified by
    enviormental variables. This functionality is **deprecated**.
    Do not rely on it as it will be removed in version 2.0.0.

    If ``--geoips-docs-path`` is not provided it defaults to
    ``$GEOIPS_PACKAGES_DIR/geoips/docs``.

    If ``--output-dir`` is not provided and ``$GEOIPS_DOCSDIR`` is set, it
    defaults to ``$GEOIPS_DOCSDIR``

