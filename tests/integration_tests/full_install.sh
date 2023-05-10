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

. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh gitlfs
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh imagemagick
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh wget
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh git
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh python
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh rclone
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_clavrx
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_abi_day
. $GEOIPS_PACKAGES_DIR/geoips/setup/check_system_requirements.sh test_data_amsr2