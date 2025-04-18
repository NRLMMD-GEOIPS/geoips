#!/bin/sh

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

geoips test sector conus
retval_conus=$?

geoips test sector global; geoips test sector goes_east
retval_all=$?

echo "CONUS retval: $retval_conus"
echo "All retval: $retval_all"
exit $((retval_conus+retval_all))