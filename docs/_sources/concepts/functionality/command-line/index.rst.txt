.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

.. _command_line:

Command Line Interface
**********************

.. _geoips:

:ref:`GeoIPS CLI <geoips>`

The GeoIPS Command Line Interface (CLI) is currently under development, but we'll keep
updated instructions in this documentation that reflect the current state of the CLI.

The GeoIPS CLI is used to interrogate / utilize GeoIPS ``artifacts`` in a user-friendly
manner. A ``GeoIPS artifact`` is an term used to reflect the chosen piece of data or
functionality implemented in GeoIPS. This could be a GeoIPS Interface, Package, Plugin,
Family, Test Script, Test Dataset, etc. that is used and/or implemented throughout the
GeoIPS Environment.

The CLI is split up into two groups as of right now. CLI commands which
:ref:`retrieve information<information_retrieval>` from GeoIPS and CLI commands which
:ref:`perform processes<performing_processes>` via GeoIPS. We'll dive into each of those
sections now.

CLI Use Cases
*************

For your ease of use, we've provided a complete  listing of all available GeoIPS CLI
commands below. This diagrams what commands are available, and the required and/or
optional arguments that go alongside these commands.

.. dropdown:: GeoIPS CLI Commands

    .. admonition:: Usage: geoips

        .. autoprogram:: geoips.commandline.commandline_interface:GeoipsCLI().parser
            :prog: geoips

.. _information_retrieval:

Information Retrieval
=====================

The GeoIPS CLI Implements two top-level commands which retrieve information about GeoIPS
artifacts based on the sub-commands provided. These two top-level commands are
``describe`` (``desc``) and ``list`` (``ls``). Each command shown below can be ran with
a ``-h`` flag to provide help instructions for the command you are running.

.. _geoips_describe:

Describe Command
----------------

:ref:`geoips describe <geoips_describe>`

``describe`` is a GeoIPS CLI command which retrieves information specific to a single
GeoIPS artifact. The purpose of any ``describe`` command is to lay out the selected
GeoIPS artifact in a verbose manner. While the outputted information may differ by each
describe  command, the ultimate purpose of each command is to provide both users and
developers detailed information about each artifact. This will help implementing their
own artifacts, and also clarify what each artifact does / needs to integrate correctly
within the GeoIPS environment. It currently implements 4 sub-commands, which we'll
describe below.

.. _geoips_describe_interface:

:ref:`geoips describe interface <geoips_describe_interface>`

``describe <interface_name>`` is a describe sub-command which retrieves information
specific to a GeoIPS interface. Information included when calling this command is:

    * Absolute Path
    * Docstring
    * Interface
    * Interface Type
    * Supported Families

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. If you want more information
about what GeoIPS Interfaces are available, run the command ``geoips list interfaces``.

::

    geoips describe alg
    geoips describe algs
    geoips describe algorithm
    geoips describe algorithms
    geoips describe <interface_name>

.. _geoips_describe_family:

:ref:`geoips describe family <geoips_describe_family>`

``describe <interface_name> family <family_name>`` (or ``fam``) is a describe
sub-command which retrieves information specific to an interface's family. Information
included when calling this command is:

    * Docstring
    * Family Name
    * Family Path
    * Interface Name
    * Interface Type
    * Required Args / Schema

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. If you want more information about
what families belong to a certain interface, run the command ``geoips list interfaces``,
which will include a column representing the supported families of each interface. You
can also run ``geoips list interfaces --columns interface supported_families`` for a
concise depiction of what families belong to each interface.

::

    geoips describe alg fam single_channel
    geoips describe algs fam single_channel
    geoips describe algorithm family single_channel
    geoips describe algorithms family single_channel
    geoips describe prod-def fam interpolator_algorithm_colormapper
    geoips describe prod-defs fam interpolator_algorithm_colormapper
    geoips describe product_default family interpolator_algorithm_colormapper
    geoips describe product_defaults family interpolator_algorithm_colormapper
    geoips describe <interface_name> family <family_name>

.. _geoips_describe_package:

:ref:`geoips describe package <geoips_describe_package>`

``describe package <package_name>`` (or ``describe pkg <package_name>``) is a describe
sub-command which retrieves information specific to a GeoIPS Package. Information
included when calling this command is:

    * Docstring
    * GeoIPS Package
    * Package Path
    * Source Code
    * Version Number

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. If you want more information about
what GeoIPS Packages are available, run the command ``geoips list packages``.

::

    geoips describe pkg geoips
    geoips describe package geoips
    geoips describe package <package_name>

.. _geoips_describe_plugin:

:ref:`geoips describe plugin <geoips_describe_plugin>`

``describe <interface_name> <plugin_name>`` is a describe sub-command which retrieves
information specific to a GeoIPS Plugin. Information included when calling this command
is:

    * Docstring
    * Family
    * Interface
    * GeoIPS Package
    * Plugin Type
    * Product Defaults (if applicable)
    * Relative Path
    * Signature (if applicable)
    * Source Names (if applicable)


For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. If you want more information about
what plugins are available, run the command ``geoips list plugins``. Note, if you are
trying to describe a product, the plugin name is a combination of it's source name and
product name. I.e. for the product ``Infrared`` coming from source ``abi``, the command
call would look like ``geoips describe product abi.Infrared``.

::

    geoips describe alg single_channel
    geoips describe algs single_channel
    geoips describe algorithm single_channel
    geoips describe algorithms single_channel
    geoips describe <interface_name> <plugin_name>

.. _geoips_list:

List Command
------------

:ref:`geoips list <geoips_list>`

``list`` is a GeoIPS CLI command which retrieves a general set of information specific
to a GeoIPS artifact type. While the outputted information may differ by each list
command, the ultimate purpose of each command is to provide both users and developers
a listing of what artifacts exist, where they can be found, and a general description
of what the artifact does. This will help users and developers gain a sense of what's,
available, where it can be found, and what has been implemented across the GeoIPS
environment. It currently implements 7 sub-commands, which we'll describe below. For any
``list`` command, there are three shared arguments: ``--long/-l``, ``--columns/-c``, and
``--package_name/-p``. You can apply any of these optional arguments to any
``geoips list`` command to specialize the output of the ``list`` command. All ``list``
commands default to a ``--long`` listing. If you only wanted specific columns to be
outputted for a ``geoips list packages`` command, you could run it like this.

.. code-block:: bash

    geoips ls pkgs --columns package docstring version
    geoips list pkgs --columns package docstring version
    geoips list packages --columns package docstring version

The command above would list all GeoIPS Plugin Packages with information including their
package name, docstring, and current version number. For a listing of what columns you
can filter by, run ``geoips list <cmd_name> --columns help``.

.. _geoips_list_interface:

:ref:`geoips list interface <geoips_list_interface>`

``list <interface_name>`` is a list sub-command which retrieves a listing of implemented

plugins of a certain interface. This can also be applied to a certain GeoIPS package.
Information included when calling this command is:

    * GeoIPS Package
    * Interface Name
    * Interface Type
    * Family
    * Plugin Name
    * Source Names (if applicable)
    * Relative Path

For an example of how to run this command, see below, one of which applies this command
to a specific package. Notice the use of aliases in case you want to use these commands
in shorthand style. To see which packages are available, run ``geoips list packages``.

::

    geoips ls alg
    geoips ls algs
    geoips list algorithm
    geoips list algorithms
    geoips list <interface_name> -p <package_name>

.. _geoips_list_interfaces:

:ref:`geoips list interfaces <geoips_list_interfaces>`

``list interfaces`` is a list sub-command which retrieves a listing of GeoIPS
interfaces. This command has two modes; ``implemented`` and ``general``. Implemented
mode searches for plugins of each interface which have been created throughout GeoIPS
packages, or a certain package. General mode retrieves a listing of native GeoIPS
Interfaces, which users can then create their own plugins using those interfaces.
General Mode cannot be package specific.
Information included when calling this command in implemented mode is:

    * GeoIPS Package
    * Interface Type
    * Interface Name

Information included when calling this command in general mode is:

    * GeoIPS Package
    * Interface Type
    * Interface Name
    * Supported Families
    * Docstring
    * Absolute Path

For an example of how to run both modes of this command, see below.

Implemented Mode Options
::

    geoips list interfaces -i
    geoips list interfaces -i -p <package_name>
    geoips list interfaces -p <package_name>

General Mode
::

    geoips list interfaces

.. _geoips_list_packages:

:ref:`geoips list packages <geoips_list_packages>`

``list packages`` (or ``list pkgs``) is a list sub-command which retrieves a listing of
GeoIPS Packages, alongside the information shown below.

    * GeoIPS Package
    * Docstring
    * Package Path
    * Version Number

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style.
::

    geoips ls pkgs
    geoips list packages

.. _geoips_list_plugins:

:ref:`geoips list plugins <geoips_list_plugins>`

``list plugins`` (or ``list plgs``) is a list sub-command which retrieves a listing of
plugins found within all, or a certain GeoIPS package. Information included when calling
this command is:

    * GeoIPS Package
    * Interface Name
    * Interface Type
    * Family
    * Plugin Name
    * Source Names
    * Relative Path

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. One of the commands below lists
plugins from a certain GeoIPS package.
::

    geoips ls plgs
    geoips list plgs
    geoips ls plugins
    geoips list plugins -p <package_name>

.. _geoips_list_scripts:

:ref:`geoips list scripts <geoips_list_scripts>`

``list scripts`` is a list sub-command which retrieves a listing of test scripts from
all, or a certain GeoIPS Package. For this command to find your test script, you must
place the script under ``<package_name>/tests/scripts/``. These test scripts can then be
ran using ``geoips run <package_name> <script_name>``. This command can only be ran if
the specified plugin package(s) are installed in *editable* mode.
Information included when calling this command is:

    * GeoIPS Package
    * Filename

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. One of the commands below lists
test scripts from a certain GeoIPS package.
::

    geoips ls scripts
    geoips list scripts
    geoips list scripts -p <package_name>

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

:ref:`geoips list test-datasets <geoips_list_test-datasets>`

``list test-datasets`` is a list sub-command which retrieves a listing of test datasets
used for testing GeoIPS processing workflows. Currently, we rely on the test-datasets
shown below to properly test GeoIPS.

List of test-datasets needed for testing GeoIPS:

    * test_data_amsr2
    * test_data_clavrx
    * test_data_fusion
    * test_data_gpm
    * test_data_noaa_aws
    * test_data_sar
    * test_data_scat
    * test_data_smap
    * test_data_viirs

Information included when calling this command is:

    * Data Host
    * Dataset Name

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style.
::

    geoips ls test-datasets
    geoips list test-datasets

.. _geoips_list_unit-tests:

:ref:`geoips list unit-tests <geoips_list_unit-tests>`

``list unit-tests`` is a list sub-command which retrieves a listing of unit tests from
all, or a certain GeoIPS Package. For this command to find your unit tets, you must
place the unit tests under ``<package_name>/tests/unit_tests/``. These test scripts can
then be ran using ``pytest -v /path/to/<package_name/tests/unit_tests/<unit_test_dir>``.
This command can only be ran if the specified plugin package(s) are installed in
*editable* mode.
Information included when calling this command is:

    * GeoIPS Package
    * Unit Test Directory
    * Unit Test Name

For an example of how to run this command, see below. Notice the use of aliases in case
you want to use these commands in shorthand style. One of the commands below lists
unit tests from a certain GeoIPS package.
::

    geoips ls unit-tests
    geoips list unit-tests -p <package_name>

.. _performing_processes:

Performing Processes
====================

The other use case of the GeoIPS CLI is for performing GeoIPS processes. We currently
implement 4 commands which perform some sort of process. This includes plugin
validation, executing test scripts, installing test datasets used by GeoIPS, and running
a processing workflow as ``run_procflow`` previously did. The latter is the most
significant change as we've rerouted all ``run_procflow`` & ``data_fusion_procflow``
commands to be sent through the GeoIPS CLI. While the GeoIPS CLI does not actually
change the implementation of how procflows were ran, this makes all procflow calls be
easily integrated as a CLI process.

Shown below are 4 types of GeoIPS Commands which will invoke processes related to
the command provided.

.. _geoips_config:

Config Command
--------------

:ref:`geoips config <geoips_config>`

Currently, GeoIPS relies on test datasets to perform testing on the processing workflows
which we've created. These test datasets are installed via a bash script before any
testing can be done. To make this process easier and more configurable, we've
implemented a ``geoips config`` (or ``geoips cfg``) command, which encapsulates
configuration settings that we can implement via the CLI.

We currently only implement the ``geoips config install <test_dataset_name>`` command
for installing test datasets, though we'll support other config commands as we continue
to develop the GeoIPS CLI.

.. _geoips_config_install:

:ref:`geoips config install <geoips_config_install>`

``config install`` installs test datasets hosted on CIRA's NextCloud instance for
testing implemented processing workflows. For a listing of test datasets available for
installation, run this command ``geoips list test-datasets``.

To install a specific test dataset, run the command below.

::

    geoips cfg install test_data_clavrx
    geoips config install test_data_clavrx
    geoips config install <test_dataset_name>

.. _geoips_run:

Run Command
-----------

.. _geoips_run_single_source:

.. _geoips_run_config_based:

.. _geoips_run_data_fusion:

:ref:`geoips run <geoips_run>`

:ref:`geoips run single source <geoips_run_single_source>`

:ref:`geoips run config_based <geoips_run_config_based>`

:ref:`geoips run data fusion <geoips_run_data_fusion>`

Currently, GeoIPS creates all outputs defined by products via a processing workflow
(procflow). These processing workflows are written as a bash script, which tells GeoIPS
what plugins will be used and how they will be processed. While this works for the time
being, we are largely refactoring the way in which outputs will be produced by using an
order-based procflow. We eventually want to specify the order in which a procflow
executes using a ``steps`` attribute in your ``product`` / ``product_defaults``.

``run`` does exactly what ``run_procflow`` and ``data_fusion_procflow`` currently do. To
preserve test scripts that were written prior to this PR, we've implemented a
``legacy run`` format which will process your test scripts the exact same manner in
which ``run_procflow`` or ``data_fusion_procflow`` did in the past. While these commands
won't point to the same entrypoint as they did before, they make use of the GeoIPS CLI
to call ``geoips run`` which will execute the same functionality as it did before.

``run`` follows the procflow defined by a bash script and produces the same output of
such bash script if it were ran ``./<script_name>``. While you technically can execute a
``run`` command directly in the commandline, we heavily suggest creating a bash script
for testing and reusability's sake. We've overwritten all ``geoips`` and ``data_fusion``
test scripts to make use of the new CLI procflow functionality. Shown below, are the
differences between executing a legacy procflow and the new CLI-based procflows. While
both work and execute the same process, we recommend transitioning your scripts to the
CLI-based method as we may remove support for legacy formats in the future.

Legacy Procflow (abi.static.Infrared.imagery_annotated.sh)

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
    retval=$?

    exit $retval

New CLI-based Procflow (abi.static.Infrared.imagery_annotated.sh)

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
    retval=$?

    exit $retval

As you can see, the only difference between the two formats is the first line and the
``--procflow`` line. With the new CLI-based format, all you need to do is replace
``run_procflow`` / ``data_fusion_procflow`` with ``geoips run <procflow_name>`` and
remove the ``--procflow`` line. That's it!

To execute the ``run`` command, just run a bash script via ``./path/to/script.sh``.

.. _geoips_test:

Test Command
------------

:ref:`geoips test <geoips_test>`

GeoIPS, and other GeoIPS packages currently implement tests to ensure that they
integrate together correctly, and that they each operate correctly at an atomic level.
While more tests are needed to ensure that every piece of GeoIPS is working fine, we
are able to get a general sense as to whether or not things are working or are broken,
and where / why that is happening.

These tests are a very useful feature, however are not that easy to run in the current
status of our codebase. To alleviate that issue, we've created a ``geoips test`` command
which can execute linting, and output / integration test scripts. Together, these
testing protocols ensure that our environment is working as expected.

Shown below, we'll demonstrate how to test each of these protocols so that the user can
easily ensure that what they're developing is working as expected. We recommend trying
to develop in a test-driven-development (TDD) manner, so that you can check that your
code is working as you develop it on the fly.

.. _geoips_test_linting:

:ref:`geoips test linting <geoips_test_linting>`

``linting`` runs the main three linters that are supported by the main GeoIPS package.
Those three linters are ``bandit``, ``black``, and ``flake8``. We may support more
linters in the future, but as this documentation was written, those are the three in
which we currently support.

To test that your code adheres to GeoIPS Linting protocols, run the command below.

::

    geoips test linting (defaults to 'geoips' package)
    geoips test linting -p <package_name>

.. _geoips_test_sector:

:ref:`geoips test sector <geoips_test_sector>`

``sector`` produces a .png image based on the provided sector plugin name. This sector
must be an entry within any Plugin Package's registered_plugins.(yaml/json) file. Once,
you've created a new sector plugin, make sure to run ``create_plugin_registries`` to get
this sector added to your registry. Once added, you can run this command to produce an
image of your sector to easily test whether or not it captures the region you expected
and if the resolution of that sector is correct.

To produce a sector image is quite simple. All you have to do is:

    * ``geoips test sector <sector_name>``

An additional output directory can be specified if you want the sector image to be saved
in a different location.

    * ``geoips test sector <sector_name> --outdir <output_directory_path>``

For example, if you were to run ``geoips test sector canada``, the following image would
be created at ``$GEOIPS_OUTDIRS/canada.png``.

.. image:: canada.png
   :width: 800

.. _geoips_test_script:

:ref:`geoips test script <geoips_test_script>`

``script`` executes an output-based test script which will return a numerical value
based on the output of the test. A 0 is a success, and any other number will denote what
failed and why that occurred. The ``script`` command can also execute ``integration``
tests (which are only supported in the 'geoips' package). These sorts of tests ensure
that all new functionality of the main GeoIPS code integrate correctly and accurately.

To run a test (bash) script, or run your integration tests, you must first place your
integration / normal test scripts in the following file locations.

    * Output Test scripts: ``<package_name>/tests/scripts/<script_name>``
    * Integration Tests: ``<package_name>/tests/integration_tests/<script_name>``

Once you've created your script in the appropriate location, follow the command below.

::

    geoips test script <script_name> (defaults to 'geoips' package)
    geoips test script -p <package_name> <script_name>
    geoips test script --integration <script_name> (no '-p' as this is only supported for 'geoips' package)

.. _geoips_tree:

Tree Command
------------

:ref:`geoips tree <geoips_tree>`

The GeoIPS CLI provides a variety of commands which aren't necessarily easily exposed
via ``geoips -h``. To improve this issue, we've added a ``geoips tree`` command which
exposes all GeoIPS CLI commands in a tree-like fashion. This way, we can expose all
commands that are available via the GeoIPS CLI, and expose the depth in which these
commands exist.

By displaying the commands in a depthwise structure, users can understand what commands
are available and how they are called.

If you just call ``geoips tree``, you'll get the full command tree in a non-colored,
verbose output.

The output of running ``geoips tree`` is shown below.

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

``geoips tree`` additionaly provides optional arguments to filter the output of this
command. Shown below are these optional arguments and descriptions of what each argument
does.

* ``--color``

  * The output of ``geoips tree`` might be a little hard to interpret. If you want the
    output of ``geoips tree`` to be highlighted by depth, make sure to use the
    ``--color`` flag. (Defaults to False)

* ``--max-depth``

  * How many levels of the tree we'd like to expose. Defaults to two levels, which is
    shown above.

* ``--short-name``

  * The output of ``geoips tree`` provides the full command string at each level. If you
    just want the literal command name and every level, make sure to provide this flag.
    (Defaults to False)

.. _geoips_validate:

Validate Command
----------------

:ref:`geoips validate <geoips_validate>`

GeoIPS runs off of plugins. While you can search the documentation and/or schemas
defined for these plugins, this is not an easy way of telling whether or not the plugin
you've created adheres to the GeoIPS protocols defined for each plugin. Every GeoIPS
interface implements validation functionality for ensuring that the plugins that
inherit from such interface work correctly. We make use of this validation functionality
from the command line, so users can easily check whether or not the plugin they've
created is valid.

``validate`` (or ``val``) follows the interface defined validation-protocol for a
certain plugin. To get a listing of plugins available for validation, run the command
``geoips list plugins -p <package_name>``, where ``-p`` is an optional flag representing
the package we want to list plugins from.

To validate a plugin we will need the full path to the plugin you want validated. See
an example of this shown below. Notice the use of aliases in case
you want to use these commands in shorthand style.

::

    geoips val /full/path/to/geoips/geoips/plugins/yaml/products/abi.yaml
    geoips validate /full/path/to/geoips/geoips/plugins/yaml/products/abi.yaml
    geoips validate /full/path/to/<pkg_name>/<pkg_name>/plugins/<plugin_type>/<interface>/plugin.<ext>
