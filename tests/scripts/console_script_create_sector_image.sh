#!/bin/sh

create_sector_image -s conus
retval_conus=$?

create_sector_image -s global goes_east -l info
retval_all=$?

echo "CONUS retval: $retval_conus"
echo "All retval: $retval_all"
exit $((retval_conus+retval_all))