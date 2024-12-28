:orphan:

.. dropdown:: Distribution Statement

 | # # # This source code is protected under the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

System Requirements
===================

GeoIPS system requirements are dependent on how you intend to use
GeoIPS. This document will outline the minimum and recommended system
requirements for users and developers for the base GeoIPS system, only.

*These requirements do not consider:*

- Running multiple concurrent GeoIPS processes.
- The requirements of plugin packages, whether official or unofficial.
- The requirements of additional software that may be used in conjunction with
  GeoIPS.
- Handling of currently unsupported data sources or formats.

If you plan to use GeoIPS with custom tooling, unsupported datsets, in a
parallel/batch environment, we recommend that you perform your own testing to
determine your requirements, especially for production settings.

Operating System and Proccessor Archetype Compatibility
-------------------------------------------------------

We officially support RedHat and Debian flavors of Linux. We aim to also support MacOS, and Windows on
both x86 and ARM processors. If you encounter an issue on Mac or Windows,
please submit an issue and while we cannot guarantee anything, we will do our best to address it.

+------------------+---------------------------------------------------------+
| Operating System | Minimum Version                                         |
+==================+=========================================================+
| Linux            | RedHat 8, AlmaLinux 8, RockyLinux 8 equivalent or later |
+------------------+---------------------------------------------------------+
|                  | Debian 10 equivalent or later                           |
+------------------+---------------------------------------------------------+
| MacOS            | 12 or later *(not officially supported)*                |
+------------------+---------------------------------------------------------+
| Windows          | 10 or later *(not officially supported)*                |
+------------------+---------------------------------------------------------+

At the moment, the installation instructions for GeoIPS (which you can find [HERE])
work for these OS/processor archetype combos:

+---------------------------+--------------------+--------------------+--------------------+------------------------+
|                           | Conda              | Expert Install     | Docker (native)    | Docker (x86 emulation) |
+===========================+====================+====================+====================+========================+
| Debian (x86)              | ✅                 | ✅                 | ✅                 | N/A                    |
+---------------------------+--------------------+--------------------+--------------------+------------------------+
| Redhat (x86)              | ✅                 | ❓                 | ❓                 | N/A                    |
+---------------------------+--------------------+--------------------+--------------------+------------------------+
| Mac (x86)                 | ❓                 | ❓                 | ❓                 | N/A                    |
+---------------------------+--------------------+--------------------+--------------------+------------------------+
| Mac (arm)                 | ❌                 | ❓                 | ❌                 | ✅                     |
+---------------------------+--------------------+--------------------+--------------------+------------------------+
| Windows with WSL2 (x86)   | ❓                 | ❓                 | ❓                 | N/A                    |
+---------------------------+--------------------+--------------------+--------------------+------------------------+

User System Requirements
------------------------

+----------+-------------+-------------+--------------------------------------+
| Hardware | Minimum     | Recommended | Comments                             |
+==========+=============+=============+======================================+
| CPU      | 2 CPU       | 4 CPU       |                                      |
+----------+-------------+-------------+--------------------------------------+
|| Memory  || 12GB       || 128GB      || RAM Requirements vary widely based  |
||         ||            ||            || on the imagery you are working with.|
+----------+-------------+-------------+--------------------------------------+
| Storage  | 20GB on SSD | 20GB on SSD || Plus additional storage, as needed, |
|          |             |             || for datasets.                       |
+----------+-------------+-------------+--------------------------------------+

Processing medium resolution next generation geostationary satellite data
(ABI, AHI) and polar orbiter satellite data with GeoIPS
requires at least 16GB memory.

High resolution next generation geostationary satellite datasets
require at least 24GB memory.

Loading all of the data from a single geostationary image from
GOES-R, Himawari, GeoKompsat, or Meteosat Third Generation (MTG)
datasets requires about 100GB.

Developer System Requirements
-----------------------------

Developers will be required to install test datasets for the GeoIPS integration
tests (40GB) and a complete, static set of Cartopy shape files (20GB). This requires
an additional 60GB of space. It is recommended that this data is placed on a local
solid state drive for speed purposes.

Operational System Requirements
-------------------------------
If you are speccing out a system for an operational environment, please reach
out to the GeoIPS team to discuss system needs and the impact of our future
development plans on your system.
