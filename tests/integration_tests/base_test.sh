# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

$GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/base_install.sh exit_on_missing
if [[ "$?" != "0" ]]; then
    exit 1
fi
echo ""

# This should contain test calls to cover ALL required functionality tests for the @package@ repo.

# The $GEOIPS tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall return value,
   # calling the test scripts appropriately, and
   # setting the final return value.

# Note you must use the variable "call" in the for the loop

# Argument to test_all_pre.sh ONLY sets the prefix on the log output / filenames.
# Used for clarity, and to differentiate potentially multiple "test_all.sh" scripts in the same repo.

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_pre.sh geoips_base

# Do not include the calls that are in "test_base_install.sh" within this list.  They are tested above.
echo ""
# "call" used in test_all_run.sh
for call in \
    "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2.config_based_no_compare.sh" \
    "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/amsr2_ocean.tc.windspeed.imagery_clean.sh" \
    "python $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_interfaces.py"
do
    . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
done

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
