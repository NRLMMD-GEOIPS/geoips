Pre Version 1.10.0a12 (2023-05-03)
**********************************

* Add plugins/\*\*.txt to pyproject.toml
* Move colormaps from geoips/image_utils/ascii_palettes to
  plugins/txt/ascii_palettes
* Add "configurable" colormap plugin (to allow fully specifying
  via call params)
* Change colormap families to "matplotlib"

Major New Functionality
=======================

Add configurable colormap plugin
--------------------------------

This plugin provides

::

  new: geoips/interfaces/module_based/sector_adjusters.py
  modified: geoips/interfaces/__init__.py

Breaking Changes
================

Move colormaps to plugins/txt/ascii_palettes
--------------------------------------------

::

  modified: pyproject.toml
  renamed: geoips/image_utils/ascii_palettes/tpw_cimss.txt -> geoips/plugins/txt/ascii_palettes/tpw_cimss.txt
  renamed: geoips/image_utils/ascii_palettes/tpw_purple.txt -> geoips/plugins/txt/ascii_palettes/tpw_purple.txt
  renamed: geoips/image_utils/ascii_palettes/tpw_pwat.txt -> geoips/plugins/txt/ascii_palettes/tpw_pwat.txt
