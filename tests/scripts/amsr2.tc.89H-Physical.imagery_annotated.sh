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
run_procflow $GEOIPS_BASEDIR/test_data/test_data_amsr2/data/20200518.062048.gcom-w1.amsr2.amsr2_nesdismanatigcom.x.x.mbt.x.e202005180759470_c202005180937100.nc \
          --procflow single_source \
          --reader_name amsr2_netcdf \
          --product_name 89H-Physical \
          --filename_format tc_fname \
          --output_format imagery_annotated \
          --boundaries_params tc_pmw \
          --gridlines_params tc_pmw \
          --metadata_filename_format metadata_default_fname \
          --metadata_output_format metadata_default \
          --trackfile_parser bdeck_parser \
          --trackfiles $GEOIPS/tests/sectors/tc_bdecks/bio012020.dat \
          --compare_path "$GEOIPS/tests/outputs/amsr2.tc.<product>.imagery_annotated" \
          --product_params_override '{"89H-Physical": {"covg_func": "center_radius", "covg_args": {"radius_km": 300}}}' \
          --output_format_kwargs '{}' \
          --filename_format_kwargs '{}' \
          --metadata_output_format_kwargs '{}' \
          --metadata_filename_format_kwargs '{}'
ss_retval=$?

exit $((ss_retval))
