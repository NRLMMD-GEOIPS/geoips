Update call signature for "trackfile" argument
----------------------------------------------

Consistent call signatures for sector_metadata_generators

::

  modified:   geoips/plugins/modules/sector_metadata_generators/bdeck_parser.py
  modified:   geoips/plugins/modules/sector_metadata_generators/tc_sector_file_parser.py

Add sector generator classes
----------------------------

::

            modified:   geoips/interfaces/__init__.py
        new file:   geoips/interfaces/module_based/sector_metadata_generators.py
        new file:   geoips/interfaces/module_based/sector_spec_generators.py


Update TC_TEMPLATE base path to updated location
------------------------------------------------

point to plugins/yaml/sectors/dynamic/tc_web_template.yaml

::

        modified:   geoips/filenames/base_paths.py

Remove old dynamic sectors
--------------------------

::

            deleted:    sectors_dynamic/tc_1024x1024/tc_1km_1024x1024.yaml
        deleted:    sectors_dynamic/tc_1024x1024/tc_2km_1024x1024.yaml
        deleted:    sectors_dynamic/tc_1400x1400/tc_1km_1400x1400.yaml
        deleted:    sectors_dynamic/tc_1400x1400/tc_2km_1400x1400.yaml
        deleted:    sectors_dynamic/tc_1600x1600/tc_2km_1600x1600.yaml
        deleted:    sectors_dynamic/tc_1600x1600/tc_4km_1600x1600.yaml
        deleted:    sectors_dynamic/tc_256x256/tc_4km_256x256.yaml
        deleted:    sectors_dynamic/tc_512x512/tc_2km_512x512.yaml
        deleted:    sectors_dynamic/tc_512x512/tc_4km_512x512.yaml
        deleted:    sectors_dynamic/tc_800x800/tc_2km_800x800.yaml
        deleted:    sectors_dynamic/tc_800x800/tc_4km_800x800.yaml
        deleted:    sectors_dynamic/tc_huge/tc_0p1km_3200x3200.yaml
        deleted:    sectors_dynamic/tc_huge/tc_1km_2500x2500.yaml
        deleted:    sectors_dynamic/tc_huge/tc_1km_3200x3200.yaml
        deleted:    sectors_dynamic/tc_web_2km_template.yaml
        deleted:    sectors_dynamic/tc_web_ascat_high_barbs_template.yaml
        deleted:    sectors_dynamic/tc_web_ascatuhr_barbs_template.yaml
        deleted:    sectors_dynamic/tc_web_halfkm_template.yaml
        deleted:    sectors_dynamic/tc_web_qkm_template.yaml
        deleted:    sectors_dynamic/tc_web_template.yaml
