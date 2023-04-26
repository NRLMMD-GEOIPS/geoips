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

Please see geoips/CHANGELOG_TEMPLATE.rst for instructions on updating
CHANGELOG appropriately with each PR

Release notes for previous/upcoming versions can be found in docs/source/releases,
for reference.

Enhancements
============

Finalize YAML plugin schema and unit tests
------------------------------------------

*From issue GEOIPS/geoips#190: 2023-04-26, Finalize YAML plugin schema and unit tests*

* Reorganized plugin schema
* Finalized schema format
* Added appropriate tests for all schema

::
    added: geoips/schema/base.yaml
    added: geoips/schema/boundaries.yaml
    added: geoips/schema/gridlines.yaml
    added: geoips/schema/product_inputs.yaml
    added: geoips/schema/product_templates/alg.yaml
    added: geoips/schema/product_templates/alg_cmap.yaml
    added: geoips/schema/product_templates/alg_interp_cmap.yaml
    added: geoips/schema/product_templates/interp.yaml
    added: geoips/schema/product_templates/interp_alg.yaml
    added: geoips/schema/product_templates/interp_alg_cmap.yaml
    added: geoips/schema/product_templates/sectored_xarray_dict_to_output_format.yaml
    added: geoips/schema/product_templates/unmodified.yaml
    added: geoips/schema/product_templates/unsectored_xarray_dict_area_to_output_format.yaml
    added: geoips/schema/product_templates/unsectored_xarray_dict_to_output_format.yaml
    added: geoips/schema/product_templates/xarray_dict_to_output_format.yaml
    added: geoips/schema/sectors_dynamic.yaml
    added: tests/test_pytest/bad_plugins/gridlines/bad_tc_windspeed_added_fields.yaml
    added: tests/test_pytest/bad_plugins/gridlines/bad_tc_windspeed_metadata_missing.yaml
    added: tests/test_pytest/bad_plugins/gridlines/bad_tc_windspeed_metadata_types.yaml
    added: tests/test_pytest/bad_plugins/gridlines/bad_tc_windspeed_spec_types.yaml
    added: tests/test_pytest/bad_plugins/gridlines/bad_tc_windspeed_wrong_fields.yaml
    added: tests/test_pytest/bad_plugins/product_templates/bad_150H_added_fields.yaml
    added: tests/test_pytest/bad_plugins/product_templates/bad_150H_metadata_missing.yaml
    added: tests/test_pytest/bad_plugins/product_templates/bad_150H_metadata_types.yaml
    added: tests/test_pytest/bad_plugins/product_templates/bad_150H_spec_types.yaml
    added: tests/test_pytest/bad_plugins/product_templates/bad_150H_wrong_fields.yaml
    added: tests/test_pytest/test_yaml_plugins.py
    deleted: geoips/schema/bases/docstring.yaml
    deleted: geoips/schema/bases/family.yaml
    deleted: geoips/schema/bases/interface.yaml
    deleted: geoips/schema/bases/name.yaml
    deleted: geoips/schema/bases/product_defaults.yaml
    deleted: geoips/schema/bases/top.yaml
    deleted: geoips/schema/bases/unvalidated.yaml
    deleted: geoips/schema/bases/valid_identifier.yaml
    deleted: geoips/schema/feature_annotators/cartopy.yaml
    deleted: geoips/schema/gridline_annotators/cartopy.yaml
    deleted: geoips/schema/product_defaults/algorithm_colormap.yaml
    deleted: geoips/schema/product_defaults/algorithm_interpolator_colormap.yaml
    deleted: geoips/schema/product_defaults/bases/algorithm.yaml
    deleted: geoips/schema/product_defaults/bases/colormap.yaml
    deleted: geoips/schema/product_defaults/bases/coverage_checker.yaml
    deleted: geoips/schema/product_defaults/bases/interpolator.yaml
    deleted: geoips/schema/product_defaults/bases/unvalidated.yaml
    deleted: geoips/schema/product_defaults/bases/windbarb_plotters.yaml
    deleted: geoips/schema/product_defaults/interpolator_algorithm.yaml
    deleted: geoips/schema/product_defaults/interpolator_algorithm_colormap.yaml
    deleted: geoips/schema/product_defaults/specs/algorithm_colormap.yaml
    deleted: geoips/schema/product_defaults/specs/algorithm_interpolator_colormap.yaml
    deleted: geoips/schema/product_defaults/specs/interpolator_algorithm.yaml
    deleted: geoips/schema/product_defaults/specs/interpolator_algorithm_colormap.yaml
    deleted: geoips/schema/product_defaults/unmodified.yaml
    deleted: geoips/schema/product_defaults/unsectored_xarray_dict_area_to_output_format.yaml
    deleted: geoips/schema/product_defaults/unsectored_xarray_dict_to_output_format.yaml
    deleted: geoips/schema/product_defaults/xarray_dict_to_output_format.yaml
    deleted: geoips/schema/products/bases/product.yaml
    deleted: geoips/schema/products/list.yaml
    deleted: geoips/schema/products/single.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/bases/docstring.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/bases/valid_identifier.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/feature_annotators/cartopy.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/gridline_annotators/cartopy.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/algorithm_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/algorithm_interpolator_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/bases/algorithm.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/bases/colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/bases/coverage_checker.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/bases/interpolator.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/interpolator_algorithm.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/product_defaults/interpolator_algorithm_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/products/bases/product.yaml
    deleted: tests/test_pytest/test_plugin_schema/bad/products/single.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/bases/valid_identifier.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/feature_annotators/cartopy.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/gridline_annotators/cartopy.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/algorithm_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/algorithm_interpolator_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/bases/algorithm.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/bases/colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/bases/coverage_checker.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/bases/interpolator.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/interpolator_algorithm.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/product_defaults/interpolator_algorithm_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/products/bases/product.yaml
    deleted: tests/test_pytest/test_plugin_schema/good/products/single.yaml
    deleted: tests/test_pytest/test_plugin_schema/good_algorithm.yaml
    deleted: tests/test_pytest/test_plugin_schema/good_product_defaults_interpolator_algorithm_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/good_product_defaults_spec_interpolator_algorithm_colormap.yaml
    deleted: tests/test_pytest/test_plugin_schema/list.yaml
    deleted: tests/test_pytest/test_plugin_schema/test_product.yaml
    deleted: tests/test_pytest/test_plugin_schema/test_yaml_schema.py
    deleted: tests/test_pytest/test_plugin_schema/test_yaml_validator.py
    modified: geoips/schema/__init__.py
    modified: geoips/schema/plugin_validator.py
    modified: pyproject.toml