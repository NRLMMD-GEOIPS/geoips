Pre Version 1.10.0a12 (2023-05-02)
**********************************

* PR specific test scripts
* Update all TC templates to use updated sectors.generated schema
* Update command line argument from tc_template_yaml to tc_spec_template

Breaking Changes
================

Update all TC templates to use updated sectors.generated formatting
-------------------------------------------------------------------

These only require sector_spec_generator specifications,
not sector_metadata_generator. Metadata is determined separately
from the area definition.

Update schema and all TC template YAMLs accordingly.

::

  modified: geoips/schema/sectors/generated.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_1024x1024/tc_1km_1024x1024.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_1024x1024/tc_2km_1024x1024.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_1400x1400/tc_1km_1400x1400.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_1400x1400/tc_2km_1400x1400.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_1600x1600/tc_2km_1600x1600.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_1600x1600/tc_4km_1600x1600.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_256x256/tc_4km_256x256.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_512x512/tc_2km_512x512.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_512x512/tc_4km_512x512.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_800x800/tc_2km_800x800.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_800x800/tc_4km_800x800.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_huge/tc_0p1km_3200x3200.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_huge/tc_1km_2500x2500.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_huge/tc_1km_3200x3200.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_web_ascat_high_barbs_template.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_web_ascatuhr_barbs_template.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_web_halfkm_template.yaml
  modified: geoips/plugins/yaml/sectors/dynamic/tc_web_template.yaml

Replace tc_template_yaml command line argument with tc_spec_template
--------------------------------------------------------------------

Now that TC templates are fully fledged plugins, reference them just based
on plugin name rather than full path to YAML file.

::

  modified: geoips/commandline/args.py
  modified: geoips/dev/output_config.py
  modified: geoips/plugins/modules/procflows/single_source.py
  modified: geoips/sector_utils/tc_tracks.py
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
