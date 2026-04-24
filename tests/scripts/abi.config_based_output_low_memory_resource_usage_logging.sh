# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash



# This produces the json resource usage statistics output files
geoips run config_based \
             --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/yaml_configs/abi_test_low_memory_resource_usage_logging.yaml
retval=$?

if [[ "$retval" != "0" ]]; then
    echo "FAILED did not complete config based processing successfully"
    echo "        To clean up statistics for a clean next run:"
    echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"
    exit $retval
fi

# This produces outputs under $GEOIPS_OUTDIRS/processing_statistics.  This is not
# currently configurable, so explicitly check there is output in these specific
# directories.
# Note to get a valid return, you'd have to clear out the processing_statistics
# directory prior to running the script.
# e.g.:
# $GEOIPS_OUTDIRS/processing_statistics/$GEOIPS_VERSION/config_based/resource_usage_checkpoints/202602/20260226/20260226.19/goes-16.abi.mixed.abi_test_low_memory_resource_usage_logging.19488.json
# $GEOIPS_OUTDIRS/processing_statistics/$GEOIPS_VERSION/config_based/overall/202602/20260226/20260226.19/goes-16.abi.mixed.abi_test_low_memory_resource_usage_logging.19488.json
# If either of these don't exist, exit 1

# Make sure the expected checkpoints statistics file was produced
globfiles="$GEOIPS_OUTDIRS/processing_statistics/*/config_based/resource_usage_checkpoints/*/*/*/goes-16.abi.mixed.abi_test_low_memory_resource_usage_logging.*.json"
ls -l $globfiles
retval=$?
if [[ "$retval" != "0" ]]; then
    echo "FAILED did not find checkpoint resource usage statistics files: $globfiles"
    echo "        To clean up statistics for a clean next run:"
    echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"
    exit $retval
fi

# Make sure the expected overall statistics file was produced
globfiles="$GEOIPS_OUTDIRS/processing_statistics/*/config_based/overall/*/*/*/goes-16.abi.mixed.abi_test_low_memory_resource_usage_logging.*.json"
ls -l $globfiles
retval=$?
if [[ "$retval" != "0" ]]; then
    echo "FAILED did not find overall resource usage statistics files: $globfiles"
    echo "        To clean up statistics for a clean next run:"
    echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"
    exit $retval
fi

# Run the plotting script
python $GEOIPS_PACKAGES_DIR/geoips/geoips/utils/memusg/plot_json_files.py \
    --json-stats-output-directory $GEOIPS_OUTDIRS/processing_statistics \
    --include-checkpoints
retval=$?

# Make sure the script completed successfully
if [[ "$retval" != "0" ]]; then
    echo "FAILED did not complete plot_json_files successfully"
    echo "        To clean up statistics for a clean next run:"
    echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"
    exit $retval
fi

# Make sure expected output was produced
# geoips_usage_stats_max_resident_set_size_gb_1.17.3_20260226T1602Z-20260227T1602Z.png
# geoips_usage_stats_system_time_1.17.3_20260226T1602Z-20260227T1602Z.png
# geoips_usage_stats_total_time_1.17.3_20260226T1602Z-20260227T1602Z.png
# geoips_usage_stats_number_products_1.17.3_20260226T1602Z-20260227T1602Z.png
globfiles="$GEOIPS_OUTDIRS/processing_statistics/plots/geoips_usage_stats_*.png"
ls -l $globfiles
retval=$?
if [[ "$retval" != "0" ]]; then
    echo "FAILED did not find resource usage plots files: $globfiles"
    echo "        To clean up statistics for a clean next run:"
    echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"
    exit $retval
fi

# Note this is currently not correctly including both the TC and static tiny sector
# in the box plot.  This will be resolved in a future PR. Checkpointing was never
# intended to be run with both TC and static sectors, so we are in the process of adding
# this support, but it is not complete.
# geoips_checkpoint_usage_stats_elapsed_time_abi_goes-16.png
globfiles="$GEOIPS_OUTDIRS/processing_statistics/plots/geoips_checkpoint_usage_stats_*.png"
ls -l $globfiles
retval=$?
if [[ "$retval" != "0" ]]; then
    echo "FAILED did not find resource usage checkpoint plots files: $globfiles"
    echo "        To clean up statistics for a clean next run:"
    echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"
    exit $retval
fi

# If we get here, then everything passed successfully
echo "SUCCESS completed config based processing, json output files produced successfully, resource usage plots produced successfully"
echo "        To clean up statistics for a clean next run:"
echo "        rm -rfv $GEOIPS_OUTDIRS/processing_statistics"

exit 0
