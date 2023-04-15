Breaking Changes
================

Update all instances of output_formats with output_formatters
-------------------------------------------------------------

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

Update all instances of filename_formats with filename_formatters
-----------------------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

::

  modified: cli.py
  modified: commandline/args.py
  modified: dev/output_config.py
  modified: filenames/duplicate_files.py
  modified: interfaces/module_based/filename_formatters.py
  modified: plugins/modules/filename_formatters/__init__.py
  modified: plugins/modules/filename_formatters/geotiff_fname.py
  modified: plugins/modules/filename_formatters/metadata_default_fname.py
  modified: plugins/modules/filename_formatters/tc_clean_fname.py
  modified: plugins/modules/filename_formatters/tc_fname.py
  modified: plugins/modules/filename_formatters/text_winds_day_fname.py
  modified: plugins/modules/filename_formatters/text_winds_full_fname.py
  modified: plugins/modules/filename_formatters/text_winds_tc_fname.py
  modified: plugins/modules/procflows/config_based.py
  modified: plugins/modules/procflows/single_source.py

Major New Functionality
=======================

Add schema for all YAML-based interfaces
----------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

* feature_annotators.cartopy

  * spec: ONLY and OPTIONAL coastlines, countries, states, rivers
  * coastlines, etc: ONLY and OPTIONAL enabled, color, and linewidth
  * Unchanged with latest update (comments only)

* gridline_annotators.cartopy

  * spec: ONLY and OPTIONAL labels, latitude-lines, longitude-lines
  * labels: ONLY and OPTIONAL top, bottom, left, right
  * lat/lon: ONLY and OPTIONAL color, linestyle, linewidth, spacing
  * Unchanged with latest update (comments only)

::

  new: geoips/schema/feature_annotators/cartopy.yaml
  new: geoips/schema/gridline_annotators/cartopy.yaml

Add YAML-based plugins with new formatting
------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

* feature_annotators

  * all currently of family "cartopy"
  * currently only support coastlines, countries, states, rivers specifications
  * Unchanged with latest update

* gridline_annotators

  * all currently of family "cartopy"
  * Currently only support color, linestyle, linewidth, spacing specifications
  * Unchanged with latest update

::

  new: geoips/plugins/yaml/feature_annotators/default.yaml
  new: geoips/plugins/yaml/feature_annotators/tc_pmw.yaml
  new: geoips/plugins/yaml/feature_annotators/tc_visir.yaml
  new: geoips/plugins/yaml/feature_annotators/tc_windspeed.yaml
  new: geoips/plugins/yaml/gridline_annotators/default.yaml
  new: geoips/plugins/yaml/gridline_annotators/tc_0p25degree.yaml
  new: geoips/plugins/yaml/gridline_annotators/tc_pmw.yaml
  new: geoips/plugins/yaml/gridline_annotators/tc_visir_3200km.yaml
  new: geoips/plugins/yaml/gridline_annotators/tc_visir.yaml
  new: geoips/plugins/yaml/gridline_annotators/tc_windspeed.yaml


Testing Updates
===============

Add bad plugins to tests/test_pytest/bad_plugins
------------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

* feature_annotators

  * Test extra field under spec (only supports coastlines, countries,
    states, rivers)
  * Test extra field under coastlines (only supports enabled, color,
    and linewidth)
  * Test non-existent family name (must be pre-defined)

* gridline_annotators

  * Test extra field under spec
  * Test extra field under labels
  * Test extra field under latitude-lines
  * Test missing metadata field
  * Test bad types in spec
  * Test nonexistent family name

::

  new: tests/test_pytest/bad_plugins/feature_annotators/bad_extra_coastlines_fields.yaml
  new: tests/test_pytest/bad_plugins/feature_annotators/bad_extra_spec_fields.yaml
  new: tests/test_pytest/bad_plugins/feature_annotators/bad_nonexistent_family.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_extra_labels_field.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_extra_latitude_field.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_extra_spec_fields.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_metadata_missing.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_metadata_types.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_nonexistent_family.yaml
  new: tests/test_pytest/bad_plugins/gridline_annotators/bad_spec_types.yaml
