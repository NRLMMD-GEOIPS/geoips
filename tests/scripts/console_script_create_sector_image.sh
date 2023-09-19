#!/bin/sh

create_sector_image conus
retval_conus=$?

create_sector_image global goes16
retval_all=$?

exit $(retval_conus+retval_all)