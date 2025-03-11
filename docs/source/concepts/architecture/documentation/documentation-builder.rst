Documentation Builder
*********************

We use ``Sphinx``, ``pinkrst`` and ``brassy`` to build our documentation.
For more information on how to use the documentation builder,
see :doc:`../../functionality/documentation-building`.

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
