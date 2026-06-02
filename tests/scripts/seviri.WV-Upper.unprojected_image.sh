# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20250624/1200/H-000-MSG3* \
             --reader_name seviri_hrit \
             --product_name WV-Upper \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "300", "y_size": "300"}' \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/seviri.WV-Upper.unprojected_image" \
             --filename_formatter geoips_fname \
             --self_register_dataset 'FULL_DISK' \
             --self_register_source seviri
retval=$?

exit $retval


