# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

if [[ "$1" == "" ]]; then
    package_name=geoips
else
    package_name=$1
fi

if [[ "$2" == "" ]]; then
    testdatadir=$GEOIPS_TESTDATA_DIR
else
    testdatadir=$2/test_data
fi

overall_start=`date +%s`

dtstr=`date -u +%Y%m%d.%H%M%S`

LOGFILE=$GEOIPS_OUTDIRS/logs/test_all/${dtstr}_${package_name}/test_all_${package_name}.log
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
