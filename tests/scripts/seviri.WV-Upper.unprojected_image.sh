# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-_________-EPI______-202004040800-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-_________-PRO______-202004040800-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000001___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000002___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000003___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000004___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000005___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000006___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000007___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-WV_062___-000008___-202004040800-C_ \
             --reader_name seviri_hrit \
             --product_name WV-Upper \
             --output_formatter unprojected_image \
             --output_formatter_kwargs '{"x_size": "1000", "y_size": "1000"}' \
             --filename_formatter geoips_fname \
             --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/seviri.WV-Upper.unprojected_image" \
             --self_register_dataset 'FULL_DISK' \
             --self_register_source seviri
retval=$?

exit $retval
