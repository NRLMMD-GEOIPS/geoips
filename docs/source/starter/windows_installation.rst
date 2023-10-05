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

************************************
Linux-based Installation for Windows
************************************

Setting up WSL through windows is the easiest method for running GeoIPS on
a Windows system.

Complete Local WSL-based GeoIPS Installation
==============================================

The following instructions will guide you through installing GeoIPS using
WSL and the linux based installation. This installation allows for a simple 
workaround of the normally difficult windows installation.

1. Setup WSL 
-----------------------------------

Follow directions on
`Microsoft WSL Install <https://learn.microsoft.com/en-us/windows/wsl/install>`_ 
which installs WSL2 and Unbuntu by default.
Note, this does require adminstrator privileges on 
the windows machine.

After a successful install and setup, run wsl and use the Linux installation
guide for installing geoips and the required Python environment:

:ref:`Complete Linux conda-based GeoIPS Installation<linux_installation`
