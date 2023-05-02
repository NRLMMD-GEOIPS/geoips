Pre Version 1.10.0a12 (2023-05-02)
**********************************

* PR specific test scripts

Breaking Changes
================

Replace tc_template_yaml command line argument with sector_spec_generator
-------------------------------------------------------------------------

Now that TC templates are fully fledged plugins, reference them just based
on plugin name rather than full path to YAML file.

::

  modified: scripts/ascat_knmi.tc.windbarbs.imagery_windbarbs_clean.sh
  modified: scripts/ascat_uhr.tc.wind-ambiguities.imagery_windbarbs.sh
  modified: scripts/atms.tc.165H.netcdf_geoips.sh
  modified: scripts/oscat_knmi.tc.windbarbs.imagery_windbarbs.sh
  modified: yaml_configs/abi_test.yaml
  modified: yaml_configs/abi_test_low_memory.yaml
  modified: yaml_configs/amsr2_test.yaml
  modified: yaml_configs/amsr2_test_low_memory.yaml

Testing Updates
===============

PR specific test scripts
------------------------

Add test script specifically including tests that *should* pass
with these updates.

::

  new file:   tests/PR_test_update_dynamic_sectors.sh
