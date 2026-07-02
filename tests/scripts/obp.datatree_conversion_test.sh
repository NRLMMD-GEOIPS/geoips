#!/bin/bash
# Test the DataTree-based OBP workflow with first-class auxiliary plugins.
#
# Requires: a full clone of the geoips repository. This test reads a bundled
# output file under tests/outputs/ and does NOT require $GEOIPS_TESTDATA_DIR
# or any externally downloaded reader test data.
#
# Usage:
#   bash tests/scripts/obp.datatree_conversion_test.sh

set -e

echo "=== DataTree OBP Conversion Test ==="

TEST_DATA="tests/outputs/abi.static.Infrared.netcdf_geoips/20200918.195020.goes-16.Infrared_latitude_longitude.test_goes16_eqc_10km_edge_night_20200918T1950Z.nc"

if [ ! -f "$TEST_DATA" ]; then
    echo "ERROR: Test data file not found: $TEST_DATA"
    echo "This test requires a full clone of the geoips repository (the file"
    echo "is bundled under tests/outputs/)."
    exit 1
fi

echo "Running workflow: test_datatree_conversions"
echo "Data: $TEST_DATA"

geoips run order_based test_datatree_conversions "$TEST_DATA"

echo "=== Test Complete ==="
