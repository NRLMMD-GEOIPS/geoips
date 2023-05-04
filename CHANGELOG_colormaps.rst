Pre Version 1.10.0a12 (2023-05-03)
**********************************

* Add plugins/\*\*.txt to pyproject.toml
* Move colormaps from geoips/image_utils/ascii_palettes to
  plugins/txt/ascii_palettes
* Add "configurable" colormap plugin (to allow fully specifying
  via call params)
* Change colormap families to "matplotlib"
* Run pytest on all installed geoips plugin packages

Major New Functionality
=======================

Allow cbar_ticks == None to plot min/max of actual data
-------------------------------------------------------

Update create_colorbar function to set cbar_ticks to cmap_norm.vmin and
cmap_norm.vmax if cbar_ticks is "None".  Additionally, ensure if the
"kwargs" options are included in mpl_colors_info, they are only used if
not None (allows including defaults for all fields in mpl_colors_info)

::

  modified:   geoips/image_utils/mpl_utils.py

Generalize matplotlib_linear_norm to allow builtin, ascii, and geoips colormaps
-------------------------------------------------------------------------------

Currently just takes the cmap_name, and through a series of try/excepts looks for
the colormap in:

1. matplotlib builtin
2. ascii palette
3. geoips plugin

::

  modified: geoips/plugins/modules/colormaps/matplotlib_linear_norm.py

Add "find_ascii_palette" routine to geoips_utils.py
---------------------------------------------------

This searches the plugin directory for plugins/txt/ascii_palettes (for now).
May tune this additionally, but for now we will hard code txt/ascii_palettes,
and require ascii colormaps to have extension .txt.

::

  modified: geoips/geoips_utils.py

Update matplotlib_linear_norm colormap plugin to support ASCII palettes
-----------------------------------------------------------------------

This plugin provides the ability to fully specify matplotlib color info
via call signature arguments.  Add options for:

* cmap_name - name of colormap to use
* cmap_source - one of "matplotlib_builtin", "geoips_module", or "ascii_palette"
* cmap_path - optional full path to ascii palette
* cbar_tick_labels - alternative labels to use if not the numeric values of
  cbar_ticks
* cbar_spacing - cbar spacing, proportional or uniform
* cbar_full_width - specify colorbar should be the full width of image
* colorbar_kwargs - pass through to matplotlib "colorbar" command
* set_ticks_kwargs - pass through to "set_ticks" command

Also add these fields to the colormap YAML schema.

Additionally, update image_utils.colormap_utils.from_ascii to take optional
"cmap_name" kwarg, if not specified, just use the basename of fname.

::

  modified: geoips/schema/product_defaults/bases/colormap.yaml
  geoips/image_utils/colormap_utils.py
  geoips/plugins/modules/colormaps/matplotlib_linear_norm.py

Breaking Changes
================

Move colormaps to plugins/txt/ascii_palettes
--------------------------------------------

Consolidating user-defined capabilities within "plugins" directory.

Add support for text ascii_palettes - which are not strictly geoips plugins
(since they will not have the required attributes, etc), but will be
accessed in a similar way.

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

All matplotlib families now have NO required params or kwargs, and a list of
available_kwargs.

::

  modified: geoips/interfaces/module_based/colormaps.py
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

Testing Updates
===============

Run pytest on all installed geoips plugin packages
--------------------------------------------------

To ensure all functionality is tested, loop through all geoips  plugin packages
when running tests/test_pytest.

::

  modified: tests/test_pytest/test_all_yaml_plugins.py
