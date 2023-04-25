Breaking Changes
================

Update all instances of user_colormaps with colormaps
-----------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified:   interfaces/module_based/colormaps.py

Update all instances of area_def_generators with sector_loaders
---------------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified: plugins/modules/procflows/single_source.py
  modified: plugins/modules/sector_loaders/__init__.py
  modified: sector_utils/tc_tracks.py
  modified: sector_utils/utils.py

Update all instances of title_formats with title_formatters
-----------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified:   cli.py
  modified:   image_utils/mpl_utils.py
  modified:   interfaces/module_based/title_formatters.py

Update all instances of interpolation with interpolators
--------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified: interfaces/module_based/interpolators.py
  modified: plugins/modules/interpolators/pyresample_wrappers/interp_gauss.py
  modified: plugins/modules/interpolators/pyresample_wrappers/interp_nearest.py
  modified: plugins/modules/interpolators/scipy_wrappers/interp_grid.py
  modified: plugins/modules/interpolators/utils/interp_pyresample.py

Update all instances of coverage_checks with coverage_checkers
--------------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified: dev/product.py
  modified: plugins/modules/coverage_checkers/__init__.py
  modified: plugins/modules/coverage_checkers/center_radius_rgba.py

Update all instances of area_def_adjusters with sector_adjusters
----------------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

Note these are actually contained in recenter_tc repo.

::

  modified: commandline/args.py
  modified: plugins/modules/procflows/config_based.py
  modified: plugins/modules/procflows/single_source.py
