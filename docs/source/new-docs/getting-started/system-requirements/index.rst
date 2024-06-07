:orphan:

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

User System Requirements
------------------------
We attempt to support Linux, MacOS, and Windows, but only officially support 
Linux. Thismeans that GeoIPS should work on all OS but we only guarantee Linux.
If you encounter an issue on Mac or Windows, please submit an issue and we will 
do our best to address it.

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

+----------+-------------+-------------+--------------------------------------+
| Hardware | Minimum     | Recommended | Supports                             |
+==========+=============+=============+======================================+
| CPU      | 2 Cores     | 4 Cores     | A single concurrent GeoIPS process   |
+----------+-------------+-------------+--------------------------------------+
|| Memory  || 12GB       || 128GB      || Production of most GeoIPS imagery.  |
||         ||            ||            || Some Geostationary imagery requires |
||         ||            ||            || > 90GB RAM.                         |
+----------+-------------+-------------+--------------------------------------+
| Storage  | 20GB on SSD | 20GB on SSD | Base GeoIPS system installation.     |
+----------+-------------+-------------+--------------------------------------+
||         || 20GB       || As needed  || Additional disk space for input and |
||         ||            ||            || output data storage. May be SDD,    |
||         ||            ||            || HDD, or NAS.                        |
+----------+-------------+-------------+--------------------------------------+

Developer System Requirements
-----------------------------

In addition to the required disk space for users, developers will require:

+----------+-------------+-------------+---------------------------+
| Hardware | Minimum     | Recommended | Supports                  |
+==========+=============+=============+===========================+
| Storage  | 40GB        | 40GB        | Integration test datasets |
+----------+-------------+-------------+---------------------------+
|          | 20GB on SSD | 20GB on SSD | Static cartopy shapefiles |
|          |             |             | for integration tests.    |
+----------+-------------+-------------+---------------------------+

Operational System Requirements
-------------------------------
If you are speccing out a system for an operational environment, please reach 
out to the GeoIPS team to discuss system needs and the impact of our future
development plans on your system.
