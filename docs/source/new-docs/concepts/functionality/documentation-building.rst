Documentation Building
**********************

We use ``Sphinx``, ``pinkrst`` and ``brassy`` to build our documentation.

Documentation can be built by calling ``python3 ./docs/build_docs.py``.

Usage
=====
Run `build_docs.py`  with the required positional arguments and optional flags:

.. code-block:: bash

    python build_docs.py [OPTIONS] <repo_path> <package_name>

**repo_path:** Path to the repository (e.g., /path/to/geoips).
Must be an existing directory and a valid Git repository.

**package_name:** Name of the package to build (e.g., geoips, data_fusion).

Optional Arguments
------------------

**--geoips-docs-path:** Path to GeoIPS documentation templates,
used when building geoips plugins.

**--license-url:** URL pointing to the license or distribution statement
for the release notes.
Defaults to ``https://github.com/NRLMMD-GEOIPS/[package_name]``.

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

Mechanism
=========

The build script does the following actions in the following order:

 #. Validates the provided ``repo_path`` exists and is a git directory
 #. Verifies the provided ``package_name`` is installed
 #. Copies build files to a temporary build directory that is deleted after the program exits
 #. Copies non-documentation files (eg. ``CODE_OF_CONDUCT.md``) into a special ``import`` directory at the top of the
 docs directory for access during building
 #. If building documentation for a plugin (aka ``package_name`` is not ``geoips``), it copies static files from the
 GeoIPS documentation directory that are needed for building
 #. Generates a top level ``index.rst`` from ``index.template.rst`` and replaces placeholder strings with actual section
 paths or removes them depending if those sections are present in the documentation.
 #. Builds release notes with brassy from sub-directories of the ``releases`` directory (any sub-directory named
 ``upcoming`` is skipped as a special case for the release process)
 #. A release index file is generated that indexes the newly generated and old ``.rst`` files in ``releases/``
 #. Sphinx's ``apidoc`` tool is used to generate ``.rst`` files for the packages Python modules
 #. Sphinx is used to build html files from the generated ``.rst`` files
 #. If everything succeeds, the built html files are copied to the specified output directory
