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
  modified: geoips/plugins/modules/colormaps/tpw/tpw_cimss.py
  modified: geoips/plugins/modules/colormaps/tpw/tpw_purple.py
  modified: geoips/plugins/modules/colormaps/tpw/tpw_pwat.py
  renamed: geoips/image_utils/ascii_palettes/tpw_cimss.txt -> geoips/plugins/txt/ascii_palettes/tpw_cimss.txt
  renamed: geoips/image_utils/ascii_palettes/tpw_purple.txt -> geoips/plugins/txt/ascii_palettes/tpw_purple.txt
  renamed: geoips/image_utils/ascii_palettes/tpw_pwat.txt -> geoips/plugins/txt/ascii_palettes/tpw_pwat.txt

Change all colormap families to "matplotlib"
--------------------------------------------

Redefining plugin familes as a collection of required_parameters,
required_kwargs, and allowable_kwargs.  This allows us to have a
collections of keyword arguments that *can* be specified for
matplotlib-based colormaps, but do not *have* to be specified.
So rather than having a different family for every combination of
tuning parameters for color specifications, have a general "matplotlib" family
that all return the "mpl_colors_info" dictionary, but can have a variable set
of arguments (depending on requirements for a specific colormap).

::

  modified: geoips/plugins/modules/colormaps/cmap_rgb.py
  modified: geoips/plugins/modules/colormaps/matplotlib_linear_norm.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_150H.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_37H.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_37H_Legacy.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_37H_Physical.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_37pct.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_89H.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_89HW.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_89H_Legacy.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_89H_Physical.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_89pct.py
  modified: geoips/plugins/modules/colormaps/pmw_tb/cmap_Rain.py
  modified: geoips/plugins/modules/colormaps/tpw/tpw_cimss.py
  modified: geoips/plugins/modules/colormaps/tpw/tpw_purple.py
  modified: geoips/plugins/modules/colormaps/tpw/tpw_pwat.py
  modified: geoips/plugins/modules/colormaps/visir/IR_BD.py
  modified: geoips/plugins/modules/colormaps/visir/Infrared.py
  modified: geoips/plugins/modules/colormaps/visir/WV.py
  modified: geoips/plugins/modules/colormaps/winds/wind_radii_transitions.py
