.. dropdown:: Distribution Statement

 This source code is protected under the license referenced at
 https://github.com/NRLMMD-GEOIPS.

.. _command_line:

Command Line Interface (CLI)
****************************

.. warning::

    The CLI is currently under development.
    The CLI may change without warning!
    Please consult this documentation for up-to-date info on the CLI.

The CLI can be used to run, configure, and test GeoIPS. It can also print lists or descriptions of available data or
functionality.

CLI commands are split up into two groups by their utility:

 - `Discovery commands`_
 - `Action commands`_

You can find the automatically created CLI usage documentation `here <./command_line_autodoc>`_.

.. contents:: Table of Contents
    :local:
    :backlinks: none

Getting Help
============

To retrieve information about the CLI's commands and arguments, the ``-h/--help`` argument can be provided at any time.
For example, each of the following will return different, context dependent, help information:

- ``geoips -h``
- ``geoips list -h``
- ``geoips list algorithms -h``
- ``geoips run -h``

Command Aliases
===============

Many GeoIPS commands and subcommands have aliases for convenience. Common aliases include:

- ``ls`` for ``list``
- ``alg`` or ``algs`` for ``algorithms``
- ``pkg`` or ``pkgs`` for ``packages``
- ``fam`` for ``family``
- ``cfg`` for ``config``
- ``val`` for ``validate``

These aliases can be used interchangeably with their full command names throughout the CLI.

Discovery Commands
==================

The CLI Implements two top-level commands that retrieve information about GeoIPS
artifacts: ``list`` and ``describe``.

list
----

``list`` returns information about a GeoIPS artifact, such as:

 - Lists of existing artifacts
 - Artifact locations
 - Artifact functionality

list interface
^^^^^^^^^^^^^^

``list interfaces`` returns a list of GeoIPS interfaces.

By default it returns the following for native interfaces:

* GeoIPS Package
* Interface Type
* Interface Name
* Supported Families
* Docstring
* Absolute Path

Implemented Mode
""""""""""""""""

The ``list interfaces`` command has an "implemented" mode.

Implemented mode searches for plugins of each
interface which have been created throughout GeoIPS
packages, or a certain package.

When running in implemented mode, it returns:

* GeoIPS Package
* Interface Type
* Interface Name

For example:

.. code-block:: bash

    geoips list interfaces -i

Both the general and implemented outputs can
be filtered by package with ``--package_name`` or ``-p``.

For example:

.. code-block:: bash

    geoips list interfaces

or

.. code-block:: bash

    geoips list interfaces -i --package_name <package_name>

list interface
^^^^^^^^^^^^^^

``list <interface_name>`` returns a list of an interface's plugins with the following plugin information:

* GeoIPS Package
* Interface Name
* Interface Type
* Family
* Plugin Name
* Source Names (if applicable)
* Relative Path

For example:

.. code-block:: bash

    geoips list algorithms

You can also filter by package name with ``--package_name`` or ``-p``. For example:

.. code-block:: bash

    geoips list interfaces --package_name geoips
    geoips list <interface_name> -p <package_name>

list packages
^^^^^^^^^^^^^

``list packages`` returns a list of GeoIPS Packages with the following package information:

* Package Name
* Docstring
* Package Path
* Version Number

For example:

.. code-block:: bash

    geoips list packages

list plugins
^^^^^^^^^^^^

``list plugins`` returns the following information about plugins:

* GeoIPS Package
* Interface Name
* Interface Type
* Family
* Plugin Name
* Source Names
* Relative Path

For example:

.. code-block:: bash

    geoips list plugins

You can filter by package with ``--package-name`` or ``-p``. For example:

.. code-block:: bash

    geoips list plugins -p <package_name>

list scripts
^^^^^^^^^^^^

``list scripts`` returns a list of test scripts implemented in GeoIPS plugin packages that are installed in editable
mode.

For each test script, this command returns:

    * GeoIPS Package
    * Filename

.. note::

    For this command to find test scripts,
    they must be `.sh` files located at ``<package_install_location>/tests/scripts/``.

.. note::

    Test scripts can be run with the `run`_ command

For example:

.. code-block:: bash

    geoips list scripts

You can filter by package with ``--package-name`` or ``-p``. For example:

.. code-block:: bash

    geoips list scripts -p <package_name>

test-datasets
^^^^^^^^^^^^^
=============
.. _geoips_list_source_names:

:ref:`geoips list source-names <geoips_list_source_names>`

``list source-names`` is a list sub-command which retrieves a listing of source_names
from all, or a certain GeoIPS Package. For this command to find a listing of
source_names, you must add a module-level ``source_names`` attribute to your reader
plugin. Every core GeoIPS reader plugin has this attribute set. We recommend following
the same method of implementation as core GeoIPS readers, as reader plugins without this
attribute will be deprecated when GeoIPS v2.0.0 is released.
Information included when calling this command is:

    * Source Name
    * Reader Names

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. One of the commands below lists
source_names from a certain GeoIPS package.
::

    geoips ls source-names
    geoips ls src-names
    geoips list source-names
    geoips list source-names -p <package_name>

.. _geoips_list_test-datasets:
``list test-datasets`` returns:

* Data Host
* Dataset Name

We require these datasets for testing GeoIPS:

* test_data_amsr2
* test_data_clavrx
* test_data_fusion
* test_data_gpm
* test_data_noaa_aws
* test_data_sar
* test_data_scat
* test_data_smap
* test_data_viirs

For example:

::

    geoips list test-datasets

unit-tests
^^^^^^^^^^

``list unit-tests`` returns a list of unit-tests from plugin packages that are installed in editable mode.

For each unit-test, the following information is returned:

* GeoIPS Package
* Unit Test Directory
* Unit Test Name

.. note::
    For this command to find your unit tests, you must
    place the unit tests under ``<package_install_location>/tests/unit_tests/``.

For example:

.. code-block:: bash

    geoips list unit-tests -p <package_name>

The output can be filtered by package with ``--package_name`` or ``-p``.
The specified plugin package(s) must be installed in editable mode.

For example, to display only the ``package`` and ``docstring``
columns from the ``geoips list packages`` command:

.. code-block:: bash

    geoips list packages --columns package docstring

Output Formatting
"""""""""""""""""

The output format can be configured with the following arguments:

 - ``--long`` or ``-l`` (the default format, a long table)
 - ``--columns`` or ``-c`` (pass column(s) to display)

For a list of what columns you can filter by,
pass ``help`` to the ``--columns`` argument.

For example:

.. code-block:: bash

    geoips list <cmd_name> --columns help

describe
--------

``describe`` retrieves detailed information about a single GeoIPS artifact. It can be used to retrieve information about
``interfaces``, ``families``, ``packages``, and ``plugins``. To provide information that is relevant and useful for each
artifact type, the information retrieved differs for different types of artifacts.

describe interface
^^^^^^^^^^^^^^^^^^

``describe <interface_name>`` retrieves information about an interface.
It returns:

* Absolute Path
* Docstring
* Interface
* Interface Type
* Supported Families

For more information about available GeoIPS Interfaces,
see the `list <#list>`_ command.

describe family
^^^^^^^^^^^^^^^

``describe <interface_name> family <family_name>`` (or ``fam``) retrieves information about a family.

It returns the following information about an interface's family:

* Docstring
* Family Name
* Family Path
* Interface Name
* Interface Type
* Required Args / Schema

For example:

.. code-block:: bash

    geoips describe prod-def fam interpolator_algorithm_colormapper

describe package
^^^^^^^^^^^^^^^^

``describe package`` retrieves information about a registered plugin package.
It returns the following information about a Package:

* Docstring
* GeoIPS Package
* Package Path
* Source Code
* Version Number

For example:

.. code-block:: bash

    geoips describe pkg geoips_clavrx

describe plugin
^^^^^^^^^^^^^^^

``describe plugin`` retrieves information about a specific plugin.
It returns the following information about a Plugin:

* Docstring
* Family Name
* Interface Name
* Interface Type
* GeoIPS Package
* Plugin Type
* Product Defaults (if applicable)
* Relative Path
* Signature (if applicable)
* Source Names (if applicable)

For example:

.. code-block:: bash

    geoips describe alg single_channel

Action Commands
===============

The CLI can kick off functionality built into GeoIPS. Below, we describe commands that
do this.

config
------

``geoips config`` (or ``geoips cfg``) makes testing easier by providing easy access to
configuration options.

.. note::

    As we continue to develop the GeoIPS CLI,
    we expect the functionality of this command to grow.

config install
^^^^^^^^^^^^^^

GeoIPS relies on test datasets to test its processing workflows.
Test datasets must be installed before tests can be run.

``config install`` installs test datasets hosted on CIRA's NextCloud instance for
testing processing workflows.

For example:

.. code-block:: bash

    geoips config install <test_dataset_name>
    geoips config install test_data_clavrx

.. note::

    To list installable test datasets,
    see ``geoips list test-datasets``.

run
---

GeoIPS creates outputs (as defined by products)
via a processing workflow, aka a procflow.

Procflows are bash scripts that call GeoIPS with configuration options.

.. warning::

    We are actively changing the way procflows work.

    This approach is problematic,
    and we are refactoring GeoIPS's procflows into an order-based framework.

    The new framework will allow users to specify the order in which a procflow
    executes via a ``steps`` attribute.

.. warning::

    ``run`` replaces ``run_procflow`` and ``data_fusion_procflow``.

    ``legacy run`` provides backwards compatibility with
    these commands by wrapping ``geoips run``

    We recommend transitioning your scripts to use ``run``
    as backwards compatibility may be removed in the future.

``run`` follows the procflow defined by a bash script and produces the same output of
such bash script if it were ran ``./<script_name>``.

Here is an example of the new CLI-based procflow,
and how it compares to the - now legacy - procflows of old.

New CLI-based Procflow (abi.static.Infrared.imagery_annotated)

.. code-block:: bash

    geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/* \
        --reader_name abi_netcdf \
        --product_name Infrared \
        --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated" \
        --output_formatter imagery_annotated \
        --filename_formatter geoips_fname \
        --resampled_read \
        --logging_level info \
        --sector_list goes_east

Legacy Procflow (abi.static.Infrared.imagery_annotated)

.. code-block:: bash

    run_procflow $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/* \
        --procflow single_source \
        --reader_name abi_netcdf \
        --product_name Infrared \
        --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated" \
        --output_formatter imagery_annotated \
        --filename_formatter geoips_fname \
        --resampled_read \
        --logging_level info \
        --sector_list goes_east

The only difference between the two examples above are the first line and the
``--procflow`` line. With the new format, all you need to do update is replace
``run_procflow`` / ``data_fusion_procflow`` with ``geoips run <procflow_name>`` and
remove the ``--procflow`` line. That's it!

test
----

GeoIPS and GeoIPS packages implement tests and linters to
confirm functionality, uniform syntax and interoperability.

``geoips test`` can execute linting, and output / integration test scripts.

Checking code often is a good practice.

test linting
^^^^^^^^^^^^

This command runs ``bandit``, ``black``, and ``flake8``.

.. note::

    We may support more linters in the future.

For example:

.. code-block:: bash

    geoips test linting # (defaults to 'geoips' package)
    geoips test linting -p <package_name> # only runs tests in provided plugin package

test sector
^^^^^^^^^^^

``sector`` produces a .png image based on the provided sector plugin name. The sector
must be an entry within any Plugin Package's registered_plugins.(yaml/json) file.

For example:

.. code-block:: bash

    geoips test sector <sector_name>

An additional output directory can be specified with ``--outdir``. For example:

    * ``geoips test sector <sector_name> --outdir <output_directory_path>``

After creating a new sector plugin, run ``create_plugin_registries``
to add the sector to your registry.

Once added, this command can produce an image to
help confirm the region and resolution of that sector.

For example, if you were to run ``geoips test sector canada``, the image below would
be saved to ``$GEOIPS_OUTDIRS/canada.png``.

.. image:: canada.png
   :width: 800

test script
^^^^^^^^^^^

``script`` executes an output-based test script which will return a numerical value
based on the output of the test.

A 0 is a success. Any non-zero number indicate a failure,
and sometimes provide information on what kind of failure occurred.

.. note::

    ``script`` only supports bash scripts ending in ``.sh``

For example:

.. code-block:: bash

    geoips test script <script_name> (defaults to 'geoips' package)

``script`` can execute integration tests in the 'geoips' package.

For example:

.. code-block:: bash

    geoips test script --integration <script_name>

To run a test script, or run your integration tests, you must first place your
integration / normal test scripts in one of these file locations:

    * Output Test scripts: ``<package_name>/tests/scripts/<script_name>``
    * Integration Tests: ``<package_name>/tests/integration_tests/<script_name>``

You can run test scripts in plugin packages by specifying the
plugin package with ``-p`` or ``--package_name``. For example:

.. code-block:: bash

    geoips test script --package_name <package_name> <script_name>
    geoips test script -p <package_name> <script_name>

tree
----

Only some GeoIPS CLI commands are exposed via ``geoips -h``.

``geoips tree`` lists all GeoIPS CLI commands in a tree-like fashion.

For example, running ``geoips tree`` returns:

.. code-block:: bash

    geoips tree

    geoips
        geoips config
            geoips config install
        geoips describe
            geoips describe algorithms
            geoips describe colormappers
            geoips describe coverage-checkers
            geoips describe feature-annotators
            geoips describe filename-formatters
            geoips describe gridline-annotators
            geoips describe interpolators
            geoips describe output-checkers
            geoips describe output-formatters
            geoips describe procflows
            geoips describe product-defaults
            geoips describe products
            geoips describe readers
            geoips describe sector-adjusters
            geoips describe sector-metadata-generators
            geoips describe sector-spec-generators
            geoips describe sectors
            geoips describe title-formatters
            geoips describe package
        geoips list
            geoips list algorithms
            geoips list colormappers
            geoips list coverage-checkers
            geoips list feature-annotators
            geoips list filename-formatters
            geoips list gridline-annotators
            geoips list interpolators
            geoips list output-checkers
            geoips list output-formatters
            geoips list procflows
            geoips list product-defaults
            geoips list products
            geoips list readers
            geoips list sector-adjusters
            geoips list sector-metadata-generators
            geoips list sector-spec-generators
            geoips list sectors
            geoips list title-formatters
            geoips list interfaces
            geoips list packages
            geoips list plugins
            geoips list scripts
            geoips list test-datasets
            geoips list unit-tests
        geoips run
            geoips run single_source
            geoips run data_fusion
            geoips run config_based
        geoips test
            geoips test linting
            geoips test script
            geoips test sector
        geoips tree
        geoips validate

``geoips tree`` provides arguments to filter its output.

* ``--color``: highlights output by depth

* ``--max-depth``: limits tree levels outputted. Defaults to two levels.

* ``--short-name``: return only literal command names

validate
--------

``validate`` (or ``val``) runs interface defined validation-protocols on plugins.

.. note::
    To list plugins available for validation, see ``geoips list plugins`` above.

A plugin's full location path is needed to validate it.

For example:

.. code-block:: bash

    geoips validate /full/path/to/geoips/geoips/plugins/yaml/products/abi.yaml
    geoips validate /full/path/to/<pkg_name>/<pkg_name>/plugins/<plugin_type>/<interface>/plugin.<ext>
