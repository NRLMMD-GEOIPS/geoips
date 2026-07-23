# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/hurricane_mindy/* \
    --reader_name abi_netcdf \
    --product_name edc-Infrared \
    --output_formatter imagery_annotated \
    --filename_formatter geoips_fname \
    --resampled_read \
    --logging_level info \
    --sector_list goes_east
retval=$?

exit $retval
