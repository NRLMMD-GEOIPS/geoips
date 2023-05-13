# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

#!/bin/bash

$GEOIPS_PACKAGES_DIR/geoips/tests/integration_tests/clavrx_install.sh exit_on_missing
if [[ "$?" != "0" ]]; then
    exit 1
fi
echo ""

# This should contain test calls to cover ALL required functionality tests for
# clavrx-based processing.

# The $GEOIPS tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall return value,
   # calling the test scripts appropriately, and
   # setting the final return value.

# Note you must use the variable "call" in the for the loop

# Argument to test_all_pre.sh ONLY sets the prefix on the log output / filenames.
# Used for clarity, and to differentiate potentially multiple "test_all.sh" scripts
# in the same repo.

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_pre.sh clavrx

# "call" used in test_all_run.sh
for call in \
    "test_interfaces" \
    "$GEOIPS_PACKAGES_DIR/geoips_clavrx/tests/scripts/ahi.Cloud-Base-Height.imagery_clean.sh"
do
    . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
done

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
