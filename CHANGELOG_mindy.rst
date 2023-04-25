Breaking Changes
================

Update all instances of output_formats with output_formatters
-------------------------------------------------------------

NOT STARTED YET.

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified: pyproject.toml
  modified: cli.py
  modified: commandline/args.py
  modified: plugins/modules/output_formatters/imagery_windbarbs_clean.py
  modified: plugins/modules/output_formatters/metadata_tc.py
  modified: plugins/modules/output_formatters/netcdf_geoips.py
  modified: plugins/modules/procflows/config_based.py
  modified: plugins/modules/procflows/single_source.py

Update all instances of output_format with output_formatter
-----------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*


(grep "output_format[^t]")

::

  modified: geoips/commandline/args.py
  modified: geoips/dev/output_config.py
  modified: geoips/dev/product.py
  modified: geoips/plugins/modules/procflows/config_based.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: tests/scripts/abi.static.Infrared.imagery_annotated.sh
  modified: tests/scripts/abi.static.Visible.imagery_annotated.sh
  modified: tests/scripts/ahi.tc.WV.geotiff.sh
  modified: tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh
  modified: tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh
  modified: tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh
  modified: tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh
  modified: tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh
  modified: tests/scripts/atms.tc.165H.netcdf_geoips.sh
  modified: tests/scripts/documentation_imagery.sh
  modified: tests/scripts/ewsg.static.Infrared.imagery_clean.sh
  modified: tests/scripts/gmi.tc.89pct.imagery_clean.sh
  modified: tests/scripts/hy2.tc.windspeed.imagery_annotated.sh
  modified: tests/scripts/imerg.tc.Rain.imagery_clean.sh
  modified: tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh
  modified: tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh
  modified: tests/scripts/modis.Infrared.unprojected_image.sh
  modified: tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh
  modified: tests/scripts/sar.tc.nrcs.imagery_annotated.sh
  modified: tests/scripts/seviri.WV-Upper.unprojected_image.sh
  modified: tests/scripts/smap.unsectored.text_winds.sh
  modified: tests/scripts/smos.tc.sectored.text_winds.sh
  modified: tests/scripts/ssmi.tc.37pct.imagery_clean.sh
  modified: tests/scripts/ssmis.color91.unprojected_image.sh
  modified: tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh
  modified: tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh
  modified: tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh
  modified: tests/yaml_configs/abi_test.yaml
  modified: tests/yaml_configs/abi_test_low_memory.yaml
  modified: tests/yaml_configs/amsr2_test.yaml
  modified: tests/yaml_configs/amsr2_test_low_memory.yaml

Update all instances of filename_formats with filename_formatters
-----------------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified: geoips/cli.py
  modified: geoips/commandline/args.py
  modified: geoips/dev/output_config.py
  modified: geoips/filenames/duplicate_files.py
  modified: geoips/interfaces/module_based/filename_formatters.py
  modified: geoips/plugins/modules/filename_formatters/__init__.py
  modified: geoips/plugins/modules/filename_formatters/geotiff_fname.py
  modified: geoips/plugins/modules/filename_formatters/metadata_default_fname.py
  modified: geoips/plugins/modules/filename_formatters/tc_clean_fname.py
  modified: geoips/plugins/modules/filename_formatters/tc_fname.py
  modified: geoips/plugins/modules/filename_formatters/text_winds_day_fname.py
  modified: geoips/plugins/modules/filename_formatters/text_winds_full_fname.py
  modified: geoips/plugins/modules/filename_formatters/text_winds_tc_fname.py
  modified: geoips/plugins/modules/procflows/config_based.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: tests/yaml_configs/abi_test.yaml
  modified: tests/yaml_configs/abi_test_low_memory.yaml
  modified: tests/yaml_configs/amsr2_test.yaml
  modified: tests/yaml_configs/amsr2_test_low_memory.yaml

Update all instances of filename_format with filename_formatter
---------------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

Replacing just the singular (after replacing plural)
(grep "filename_format[^t]")

::

  modified: geoips/commandline/args.py
  modified: geoips/dev/output_config.py
  modified: geoips/filenames/duplicate_files.py
  modified: geoips/plugins/modules/procflows/config_based.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: tests/scripts/abi.static.Infrared.imagery_annotated.sh
  modified: tests/scripts/abi.static.Visible.imagery_annotated.sh
  modified: tests/scripts/ahi.tc.WV.geotiff.sh
  modified: tests/scripts/amsr2.tc.89H-Physical.imagery_annotated.sh
  modified: tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh
  modified: tests/scripts/amsub_mirs.tc.183-3H.imagery_annotated.sh
  modified: tests/scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh
  modified: tests/scripts/ascat_low_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: tests/scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh
  modified: tests/scripts/atms.tc.165H.netcdf_geoips.sh
  modified: tests/scripts/documentation_imagery.sh
  modified: tests/scripts/ewsg.static.Infrared.imagery_clean.sh
  modified: tests/scripts/gmi.tc.89pct.imagery_clean.sh
  modified: tests/scripts/hy2.tc.windspeed.imagery_annotated.sh
  modified: tests/scripts/imerg.tc.Rain.imagery_clean.sh
  modified: tests/scripts/mimic_coarse.static.TPW-CIMSS.imagery_annotated.sh
  modified: tests/scripts/mimic_fine.tc.TPW-PWAT.imagery_annotated.sh
  modified: tests/scripts/modis.Infrared.unprojected_image.sh
  modified: tests/scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: tests/scripts/saphir.tc.183-3HNearest.imagery_annotated.sh
  modified: tests/scripts/sar.tc.nrcs.imagery_annotated.sh
  modified: tests/scripts/seviri.WV-Upper.unprojected_image.sh
  modified: tests/scripts/smap.unsectored.text_winds.sh
  modified: tests/scripts/smos.tc.sectored.text_winds.sh
  modified: tests/scripts/ssmi.tc.37pct.imagery_clean.sh
  modified: tests/scripts/ssmis.color91.unprojected_image.sh
  modified: tests/scripts/viirsclearnight.Night-Vis-IR-GeoIPS1.unprojected_image.sh
  modified: tests/scripts/viirsday.tc.Night-Vis-IR.imagery_annotated.sh
  modified: tests/scripts/viirsmoon.tc.Night-Vis-GeoIPS1.imagery_clean.sh

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
