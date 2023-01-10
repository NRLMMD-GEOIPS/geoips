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

#!/bin/sh

# This should contain test calls to cover ALL required functionality tests for the geoips repo.

# The $GEOIPS_PACKAGES_DIR/geoips tests modules sourced within this script handle:
   # setting up the appropriate associative arrays for tracking the overall return value,
   # calling the test scripts appropriately, and
   # setting the final return value.

# Note you must use the variable "call" in the for the loop

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_pre.sh geoips_base

echo ""
# "call" used in test_all_run.sh
for call in \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.config_based_output.sh" \
            "$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/abi.static.Visible.imagery_annotated.sh" \
            "test_interfaces"
do
    . $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_run.sh
done

. $GEOIPS_PACKAGES_DIR/geoips/tests/utils/test_all_post.sh
