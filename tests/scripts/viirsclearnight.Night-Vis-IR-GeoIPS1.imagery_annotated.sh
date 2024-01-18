# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.

run_procflow $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20240117/172400/VNP02DNB.A2024017.1724.002.2024018012054.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20240117/172400/VNP02IMG.A2024017.1724.002.2024018012054.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20240117/172400/VNP02MOD.A2024017.1724.002.2024018012054.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20240117/172400/VNP03DNB.A2024017.1724.002.2024018003923.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20240117/172400/VNP03IMG.A2024017.1724.002.2024018003923.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20240117/172400/VNP03MOD.A2024017.1724.002.2024018003923.nc \
             --procflow single_source \
             --reader_name viirs_netcdf \
             --product_name Night-Vis-IR-GeoIPS1 \
             --output_formatter imagery_annotated \
             --filename_formatter geoips_fname \
             --sector_list north_pole \
             --gridline_annotator north_pole \
             --minimum_coverage 0 \
             --no_presectoring \
             --logging_level info

ss_retval=$?

exit $((ss_retval))

            #  --self_register_dataset 'DNB' \
            #  --self_register_source viirs \