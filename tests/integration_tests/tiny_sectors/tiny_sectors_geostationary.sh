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
      * usually Test-*-Day-Only, or -Night-Only for
        efficiency reasons and consistency and optimum evaluation of the contents
        of the data/sector, but could be any product.
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
if [[ "$GEOIPS_TEST_SECTOR_CREATE_GEOTIFF_OUTPUTS" == "True" ]]; then
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

# Optional imagery_annotated output, for reference.
# This is really only used for evaluation / reference purposes, so just allow turning
# it on manually with an environment variable.  Typically will NOT be used (to avoid
# duplicating tiny sector test time, by unnecessarily running both imagery_annotated and
# imagery_clean output), but keep it in the same script with the tiny sector
# imagery_clean comparison tests to ensure the exact same output is produced as
# imagery_annotated if desired for reference purposes. Produce BOTH Day-Only and
# Night-Only versions of the tiny sector (assumed that one of Day-Only or Night-Only
# was requested - should always use Day-Only or Night-Only products for tiny sectors
# for clarity).
if [[ "$GEOIPS_TEST_SECTOR_CREATE_ANNOTATED_OUTPUTS" == "True" ]]; then
    # Run both day and night annotated tiny sectors, better evaluation of
    # what's in there.
    orig_product_name=$product_name
    if [[ "$product_name" == *"Night"* ]]; then
        opposite_product_name="${product_name/Night/Day}"
    elif [[ "$product_name" == *"Day"* ]]; then
        opposite_product_name="${product_name/Day/Night}"
    fi
    geoips run single_source $files \
                 --reader_name $reader_name \
                 --reader_kwargs '{"satellite_zenith_angle_cutoff": None}' \
                 --product_name $orig_product_name \
                 --output_formatter imagery_annotated \
                 --output_formatter_kwargs '{"title_copyright": "Tiny Sector Test Product"}' \
                 --filename_formatter geoips_fname \
                 --filename_formatter_kwargs '{"extra": "orig_annotated"}' \
                 --logging_level info \
                 --minimum_coverage 0 \
                 --resampled_read \
                 --sector_list $test_sector_name
    geoips run single_source $files \
                 --reader_name $reader_name \
                 --reader_kwargs '{"satellite_zenith_angle_cutoff": None}' \
                 --product_name $opposite_product_name \
                 --output_formatter imagery_annotated \
                 --output_formatter_kwargs '{"title_copyright": "Opposite Product"}' \
                 --filename_formatter geoips_fname \
                 --filename_formatter_kwargs '{"extra": "opposite_annotated"}' \
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

######################################################################################
# Copy to example_test_imagery_outputs for reference.
# This is not part of the tests, and will not cause the script to fail if nothing is found.
mkdir -p $GEOIPS_OUTDIRS/example_test_imagery_outputs
found_one=False
# Check all geostationary sensors for outputs.
for curr_sensor in "abi" "ahi" "ami" "seviri" "fci"; do
    for curr_product_name in "$orig_product_name" "$opposite_product_name"; do
        # Note tiny sectors go in Tests- and not Global- directories
        fname_glob=$GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Tests-*/x-x-x/${curr_product_name}/${curr_sensor}/*${curr_product_name}*.png
        # Check if there are any files matching the glob, if so copy them over.
        ls -l $fname_glob >& /dev/null
        if [[ $? == 0 ]]; then
            echo ""
            echo "***********"
            echo "***Found product $curr_product_name for sensor $curr_sensor!"
            echo "***********"
            echo ""
            found_one=True
            cp -pv $fname_glob $GEOIPS_OUTDIRS/example_test_imagery_outputs
        fi
    done
done

echo ""
if [[ "$found_one" == "True" ]]; then
    echo "***********"
    echo "Copied output files to $GEOIPS_OUTDIRS/example_test_imagery_outputs"
    echo "***********"
fi
if [[ "$found_one" == "False" ]]; then
    echo "***********"
    echo "No output files found!  Not copied to $GEOIPS_OUTDIRS/example_test_imagery_outputs!"
    echo "***********"
fi
echo ""
echo "***********"
echo "To review all example test imagery outputs:"
echo "  ls -lthr $GEOIPS_OUTDIRS/example_test_imagery_outputs/*"
echo "***********"
######################################################################################

exit $retval
