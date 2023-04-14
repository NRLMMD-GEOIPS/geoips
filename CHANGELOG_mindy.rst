
Major New Functionality
=======================

Update schema for all YAML-based interfaces
-------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

* feature_annotators.cartopy

  * spec: coastlines, countries, states, rivers only
  * coastlines, etc: enabled, color, and linewidth ONLY

::

  geoips/schema/feature_annotators/cartopy.yaml

Update YAML-based plugins for new formatting
--------------------------------------------

*From issue NRLMMD-GEOIPS/geoips#165: 2023-04-14, update interface names*

* feature_annotators

  * all currently of family "cartopy"
  * currently only support coastlines, countries, states, rivers specifications
  * unmodified with latest update to schema.

::

  new: default.yaml
  new: tc_pmw.yaml
  new: tc_visir.yaml
  new: tc_windspeed.yaml


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

::

  new: tests/test_pytest/bad_plugins/feature_annotators/bad_extra_coastlines_fields.yaml
  new: tests/test_pytest/bad_plugins/feature_annotators/bad_extra_spec_fields.yaml
  new: tests/test_pytest/bad_plugins/feature_annotators/bad_nonexistent_family.yaml
