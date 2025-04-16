.. dropdown:: Distribution Statement

 | # # # This source code is subject to the license referenced at
 | # # # https://github.com/NRLMMD-GEOIPS.

Linux-based Installation for Windows
************************************

Setting up WSL through windows is the easiest method for running GeoIPS on
a Windows system.

Complete Local WSL-based GeoIPS Installation
============================================

The following instructions will guide you through installing GeoIPS using
WSL and the linux based installation. This installation allows for a simple
workaround of the normally difficult windows installation.

1. Setup WSL
------------

Follow directions on
`Microsoft WSL Install <https://learn.microsoft.com/en-us/windows/wsl/install>`_
which installs WSL2 and Unbuntu by default.
Note, this does require adminstrator privileges on
the windows machine.

After a successful install and setup, run wsl and use the Linux installation
guide for installing geoips and the required Python environment:

:ref:`Complete Linux conda-based GeoIPS Installation<linux-installation>`
