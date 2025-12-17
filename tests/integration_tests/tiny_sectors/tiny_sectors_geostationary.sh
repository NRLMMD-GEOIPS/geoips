# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

if [[ "$1" == "" && "$2" == "" && "$3" == "" && "$4" == "" ]]; then
    echo """
    Usage $0 [test_sector_name] [reader_name] [product_name] [repo_name] [files]

    Wrapper test script to produce specified tiny sector output, and compare it with
    the stored comparison output imagery.
    Typically used from tests/integration_tests/test_tiny_sectors_reponame.py

    It always produces
    * imagery_clean output
    * geoips_fname filename formatter,
    * --compare_path "$GEOIPS_PACKAGES_DIR/${repo_name}/tests/integration_tests/tiny_sectors/outputs/${test_sector_name}_${product_name}"
    * satellite zenith angle cutoff None,

    with the following arguments passed in:

    * test_sector_name
      * Usually of format test_SATELLITE_PROJ_RES_FEAT_DAYNIGHT_YYYYMMDDTHHMNZ
      * e.g. test_goes16_eqc_3km_edge_day_20200918T1950Z
      * e.g. test_goeswest_eqc_3km_nadir
    * reader_name
    * product_name
      * usually Test-*-Day-Only, -Night-Only, or -Day-Night for
        efficiency reasons and consistency, but could be any product.
    * repo_name
    * data_files
    """
fi

# Default values - if you do not have this exact test case available, call with available data files / sectors.

# This exact test case required for valid comparisons - remove "compare_path" argument if running a different
# set of arguments.
test_sector_name=$1
shift
reader_name=$1
shift
product_name=$1
shift
repo_name=$1
shift
files=$@

# test_sector_name=test_goes16_eqc_3km_edge_day_20200918T1950Z
# reader_name=abi_netcdf
# product_name="Test-ABI-B14-Day-Only"
# files="$GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/*"

# Optional geotiff output, for reference.
# This is really only used for evaluation / reference purposes, so just allow turning
# it on manually with an environment variable.  Typically will NOT be used (to avoid
# duplicating tiny sector test time, by unnecessarily running both geotiff and
# imagery_clean output), but keep it in the same script with the tiny sector
# imagery_clean comparison tests to ensure the exact same output is produced as
# geotiff if desired for reference purposes.
if [[ "$GEOIPS_CREATE_TINY_SECTOR_TEST_GEOTIFF_OUTPUTS" == "True" ]]; then
    geoips run single_source $files \
                 --reader_name $reader_name \
                 --reader_kwargs '{"satellite_zenith_angle_cutoff": None}' \
                 --product_name $product_name \
                 --output_formatter cogeotiff \
                 --filename_formatter geotiff_fname \
                 --logging_level info \
                 --minimum_coverage 0 \
                 --resampled_read \
                 --sector_list $test_sector_name
fi

geoips run single_source $files \
             --reader_name $reader_name \
             --reader_kwargs '{"satellite_zenith_angle_cutoff": None}' \
             --product_name $product_name \
             --compare_path "$GEOIPS_PACKAGES_DIR/${repo_name}/tests/integration_tests/tiny_sectors/outputs/${test_sector_name}_${product_name}" \
             --output_formatter imagery_clean\
             --filename_formatter geoips_fname \
             --minimum_coverage 0 \
             --resampled_read \
             --sector_list $test_sector_name
retval=$?

exit $retval
