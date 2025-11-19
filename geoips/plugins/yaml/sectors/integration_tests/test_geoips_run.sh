# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $4 \
    --reader_name $3 \
    --product_name $2 \
    --output_formatter cogeotiff \
    --filename_formatter geotiff_fname \
    --logging_level info \
    --resampled_read \
    --sector_list $1
retval=$?

exit $retval


            #  --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_annotated_enhanced" \
