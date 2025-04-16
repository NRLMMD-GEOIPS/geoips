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

echo "Deleting bad files from test repos"
# Include 2 levels - some repos have a subdirectory organization.
for fname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/diff_test_output*/rm_*; do source $fname; done
for fname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/diff_test_output*/rm_*; do source $fname; done
for fname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/*/diff_test_output*/rm_*; do source $fname; done
for fname in $GEOIPS_TESTDATA_DIR/$repo_name/outputs/*/*/*/*/diff_test_output*/rm_*; do source $fname; done

for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/diff_test_output*/rm_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/diff_test_output*/rm_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/diff_test_output*/rm_*; do source $fname; done
for fname in $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs/*/*/*/*/diff_test_output*/rm_*; do source $fname; done

# Get rid of all the comparison files in preparation for commiting new/removed/modified files
$GEOIPS_PACKAGES_DIR/geoips/tests/utils/delete_diff_dirs.sh $repo_name

echo "Now go to the individual "
echo "    $GEOIPS_TESTDATA_DIR/$repo_name/outputs"
echo "    $GEOIPS_PACKAGES_DIR/$repo_name/tests/outputs"
echo "directories and add/commit new/removed/modified files"
