# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-_________-EPI______-202312110800-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-_________-PRO______-202312110800-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000001___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000002___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000003___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000004___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000005___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000006___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000007___-202312110800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/H-000-MSG2__-MSG2_IODC___-WV_062___-000008___-202312110800-C_ \
             --reader_name seviri_hrit \
             --product_name WV-Upper \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "1000", "y_size": "1000"}' \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/seviri.WV-Upper.unprojected_image" \
             --filename_formatter geoips_fname \
             --self_register_dataset 'FULL_DISK' \
             --self_register_source seviri
retval=$?

exit $retval


