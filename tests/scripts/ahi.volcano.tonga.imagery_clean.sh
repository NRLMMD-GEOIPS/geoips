# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips run single_source \
    ${GEOIPS_TESTDATA_DIR}/test_data_ahi/data/tonga_20220115T0430/* \
    --reader_name ahi_hsd \
    --product_name Infrared \
    --filename_formatter geoips_fname \
    --output_formatter imagery_clean \
    --compare_path "$GEOIPS_PACKAGES_DIR/geoips/tests/outputs/ahi.tonga.volcano" \
    --trackfile_parser volc_parser \
    --trackfiles $GEOIPS/tests/sectors/volc_csv/tonga_trackfile.csv \
    --tc_spec_template volc_tonga

retval=$?

exit $retval

