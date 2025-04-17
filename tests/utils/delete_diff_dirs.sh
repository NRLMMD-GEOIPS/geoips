# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

if [[ "$1" == "" ]]; then
    echo ""
    echo "Usage: $0 <repo_name>"
    echo ""
    echo "Where <repo_name> either"
    echo "    $GEOIPS_PACKAGES_DIR/<repo_name>"
    echo "    $GEOIPS_TESTDATA_DIR/<repo_name>"
    exit 1
fi

repo_name=$1

echo "Deleting comparison files from test repos"
# This will delete all test comparison files - the full directories as well as the individual files at the top level.
# This is in preparation for updating all the test repos - assume we're done with all comparison files at this point.
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/*diff_test_output*
rm -rfv $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/*diff_test_output*

rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*diff_test_output*
rm -rfv $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*diff_test_output*

