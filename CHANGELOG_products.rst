Pre Version 1.10.0a12 (2023-05-05)
**********************************

* Allow passing dictionary of product_spec_overrides to products.get_plugin
* Support multiple coverage checkers for a single product
* Bug fixes
* Add data_fusion stitched test to test_full_install.sh

Refactoring
===========

Allow passing dictionary of product_spec_overrides to products.get_plugin
-------------------------------------------------------------------------

When opening a product plugin, if optional "product_spec_override" is passed
to the get_plugin method, use the values contained within product_spec_override
in place of those found in products and product_defaults.

This replaces the "product_params_override" used with the deprecated product
interface.

::

  modified: geoips/commandline/args.py
  modified: geoips/interfaces/yaml_based/products.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh
  modified: tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh
  modified: tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh
  modified: tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh
  modified: tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh
  modified: tests/scripts/atms.tc.165H.netcdf_geoips.sh
  modified: tests/scripts/gmi.tc.89pct.imagery_clean.sh
  modified: tests/scripts/hy2.tc.windspeed.imagery_annotated.sh
  modified: tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh
  modified: tests/scripts/sar.tc.nrcs.imagery_annotated.sh
  modified: tests/scripts/ssmi.tc.37pct.imagery_clean.sh
  modified: tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh
  modified: tests/yaml_configs/amsr2_test.yaml
  modified: tests/yaml_configs/amsr2_test_low_memory.yaml

Support multiple coverage checkers for a single product
-------------------------------------------------------

* Add filename_coverage_checker, full_coverage_checker, and
  image_production_coverage_checker to product_defaults schema
* Pass output_dict["product_spec_override"] to all products.get_plugin calls.

::

  modified: geoips/plugins/modules/procflows/config_based.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: geoips/dev/output_config.py
  modified: geoips/plugins/modules/filename_formatters/utils/tc_file_naming.py
  modified: geoips/plugins/modules/output_formatters/imagery_annotated.py
  modified: geoips/plugins/modules/output_formatters/metadata_tc.py
  modified: geoips/schema/product_defaults/specs/algorithm_colormap.yaml
  modified: geoips/schema/product_defaults/specs/algorithm_interpolator_colormap.yaml
  modified: geoips/schema/product_defaults/specs/interpolator_algorithm.yaml
  modified: geoips/schema/product_defaults/specs/interpolator_algorithm_colormap.yaml

Bug Fixes
=========

Fix plugin names in product_defaults
------------------------------------

* Update range->output_data_range in Infared-Gray product_defaults
* pmw_tc.pmw_->pmw_ algorithm name in PMW product_defaults

::

  modified: plugins/yaml/product_defaults/pmw_37/37pct.yaml
  modified: plugins/yaml/product_defaults/pmw_37/37pctNearest.yaml
  modified: plugins/yaml/product_defaults/pmw_89/color89.yaml
  modified: plugins/yaml/product_defaults/pmw_89/color89Nearest.yaml
  modified: plugins/yaml/product_defaults/visir/Infrared-Gray.yaml

Fix typo in overlay imagery setup
---------------------------------

* kwargs["bg_array"] -> kwargs["bg_xarray"].source_name
* Add "from geoips.interfaces import products" to metadata_tc output
* Fix coverage_checker plugin call in metadata_tc output

::

  modified:   geoips/dev/output_config.py
  modified:   geoips/plugins/modules/output_formatters/metadata_tc.py


Testing Updates
===============

Add data_fusion stitched test to test_full_install.sh
-----------------------------------------------------

Add NOAA AWS pull of goes16, goes17, and himawari8 to
test_data_fusion.

Update data_fusion test call to run test_all.sh vs just layered.sh

::

  modified:   setup.sh
  modified:   tests/test_full_install.sh
