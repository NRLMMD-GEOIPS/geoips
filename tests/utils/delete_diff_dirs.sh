# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

#!/bin/bash

if [[ "$1" == "" ]]; then
    echo ""
    echo "Usage: $0 <repo_name>"
    echo ""
    echo "Where <repo_name> either"
    echo "    $GEOIPS_PACKAGES_DIR/<repo_name>"
    echo "    $GEOIPS_BASEDIR/test_data/<repo_name>"
    exit 1
fi

repo_name=$1

echo "Deleting comparison files from test repos"
# This will delete all test comparison files - the full directories as well as the individual files at the top level.
# This is in preparation for updating all the test repos - assume we're done with all comparison files at this point.
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*/*/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*/*/*diff_test_output*
rm -rfv $GEOIPS_BASEDIR/test_data/$repo_name/outputs/*/*/*diff_test_output*

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

