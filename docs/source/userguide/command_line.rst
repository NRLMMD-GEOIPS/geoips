 | # # # Distribution Statement A. Approved for public release. Distribution unlimited.
 | # # #
 | # # # Author:
 | # # # Naval Research Laboratory, Marine Meteorology Division
 | # # #
 | # # # This program is free software: you can redistribute it and/or modify it under
 | # # # the terms of the NRLMMD License included with this program. This program is
 | # # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 | # # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
 | # # # for more details. If you did not receive the license, for more information see:
 | # # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

.. _command_line:

**********************
Command Line Interface
**********************

The GeoIPS Command Line Interface (CLI) is currently under development, but we'll keep
updated instructions in this documentation that reflect the current state of the CLI.

The GeoIPS CLI is used to interrogate / utilize GeoIPS ``artifacts`` in a user-friendly
manner. A ``GeoIPS artifact`` is an term used to reflect the chosen piece of data or
functionality implemented in GeoIPS. This could be a GeoIPS Interface, Package, Plugin,
Family, Test Script, Test Dataset, etc. that is used and/or implemented throughout the
GeoIPS Environment.

The CLI is split up into two groups as of right now. CLI commands which
:ref:`retrieve information<information_retrieval>` from GeoIPS and CLI commands which
:ref:`perform processes<process_performing>` via GeoIPS. We'll dive into each of those
sections now.

CLI Use Cases
*************

.. _information_retrieval:

Information Retrieval
=====================

The GeoIPS CLI Implements two top-level commands which retrieve information about GeoIPS
artifacts based on the sub-commands provided. These two top-level commands are ``get``
and ``list``. Each command shown below can be ran with a ``-h`` flag to provide help
instructions for the command you are running.

Get Command
-----------

``get`` is a GeoIPS CLI command which retrieves information specific to a single GeoIPS
artifact. The purpose of any ``get`` command is to describe the selected GeoIPS artifact
in a verbose manner. While the outputted information may differ by each get command, the
ultimate purpose of each command is to provide both users and developers detailed
information about each artifact. This will help implementing their own artifacts, and
also clarify what each artifact does / needs to intergrate correctly within the GeoIPS
environment. It currently implements 4 sub-commands, which we'll describe below.

``get family`` is a get sub-command which retrieves information specific to an
interface's family. Information included when calling this command is:

    * Docstring
    * Family Name
    * Interface Name
    * Interface Type
    * Required Args / Schema

For an example of how to run this command, see below. If you want more information about
what families belong to a certain interface, run the command ``geoips list interfaces``,
which will include a column representing the supported families of each interface.

::

    geoips get family algorithms single_channel

``get interface`` is a get sub-command which retrieves information specific to a GeoIPS
interface. Information included when calling this command is:

    * Absolute Path
    * Docstring
    * Interface
    * Interface Type
    * Supported Families

For an example of how to run this command, see below. If you want more information about
what GeoIPS Interfaces are available, run the command ``geoips list interfaces``.

::

    geoips get interface algorithms

``get package`` is a get sub-command which retrieves information specific to a GeoIPS
Package. Information included when calling this command is:

    * Docstring
    * Documentation Link
    * GeoIPS Package
    * Package Path

For an example of how to run this command, see below. If you want more information about
what GeoIPS Packages are available, run the command ``geoips list packages``.

::

    geoips get package recenter_tc

``get plugin`` is a get sub-command which retrieves information specific to a GeoIPS
Plugin. Information included when calling this command is:

    * Docstring
    * Family
    * Interface
    * GeoIPS Package
    * Plugin Type
    * Relative Path

For an example of how to run this command, see below. If you want more information about
what plugins are available, run the command ``geoips list plugins``.

::

    geoips get plugin algorithms single_channel

List Command
------------

``list`` is a GeoIPS CLI command which retrieves a general set of information specific
to a GeoIPS artifact type. While the outputted information may differ by each list
command, the ultimate purpose of each command is to provide both users and developers
a listing of what artifacts exist, where they can be found, and a general description
of what the artifact does. This will help users and developers gain a sense of what's,
available, where it can be found, and what has been implemented across the GeoIPS
environment. It currently implements 5 sub-commands, which we'll describe below.

``list interface`` is a list sub-command which retrieves a listing of implemented
plugins of a certain interface. This can also be applied to a certain GeoIPS package.
Information included when calling this command is:

    * Family Name
    * GeoIPS Packages
    * Interface Name
    * Interface Type
    * Plugin Name
    * Relative Path

For an example of how to run this command, see below, one of which applies this command
to a specific packages. To see which packages are available, run
``geoips list packages``.

::

    geoips list interface algorithms
    geoips list interface algorithms -p _package_name_

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

    * Absolute Path
    * Docstring
    * GeoIPS Package
    * Interface Name
    * Interface Type
    * Supported Families

For an example of how to run both modes of this command, see below.

Implemented Mode Options
::

    geoips list interfaces -i
    geoips list interfafes -i -p _package_name_

General Mode
::

    geoips list interfaces

``list packages`` is a list sub-command which retrieves a listing of GeoIPS Packages,
alongside the information shown below.

    * Docstring
    * GeoIPS Package
    * Package Path

For an example of how to run this command, see below.
::

    geoips list packages

``list plugins`` is a get sub-command which retrieves a listing of plugins found within
all, or a certain GeoIPS package. Information included when calling this command is:

    * GeoIPS Package
    * Family Name
    * Interface Name
    * Interface Type
    * Plugin Name
    * Relative Path

For an example of how to run this command, see below. One of the commands below lists
plugins from a certain GeoIPS package.
::

    geoips list plugins
    geoips list plugins -p _package_name_

``list scripts`` is a list sub-command which retrieves a listing of test scripts from
all, or a certain GeoIPS Package. For this command to find your test script, you must
place the script under ``_package_name_/tests/scripts/``. These test scripts can then be
ran using ``geoips run _package_name_ _script_name_``.
Information included when calling this command is:

    * GeoIPS Package
    * File Name

For an example of how to run this command, see below. One of the commands below lists
test scripts from a certain GeoIPS package.
::

    geoips list scripts
    geoips list scripts -p _package_name_

.. _process_performing: