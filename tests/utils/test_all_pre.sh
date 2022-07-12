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

if [[ "$1" == "" ]]; then
    package_name=geoips
else
    package_name=$1
fi

if [[ "$2" == "" ]]; then
    basedir=$GEOIPS_BASEDIR
else
    basedir=$2
fi

overall_start=`date +%s`

dtstr=`date -u +%Y%m%d.%H%M%S`

LOGFILE=$basedir/test_data/logs/`date -u +%Y%m%d`/${dtstr}_${package_name}/test_all_${package_name}.log
mkdir -p `dirname $LOGFILE`

echo `date` Running pre, log: $LOGFILE

echo $LOGFILE > $LOGFILE 2>&1

overall_procflow_retval=0
overall_procflow_retvals=()
overall_failed_products=()
overall_attempted_products=()
overall_successful_products=()
overall_runtimes=()
overall_calls=()
overall_num=0
