# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# This script calls pytest with standard arguments, and redirects output to
# $GEOIPS_OUTDIRS/logs/pytests.  Called as either:
#     interactive_test.sh base_test
#         # CALLS pytest -m "integration and base" $repopath
#     interactive_test.sh full_test
#         # CALLS pytest -m "integration and full" $repopath

repopath=`dirname $0`/../../
repopath=`realpath $repopath`
test_name="$1"

if [[ "$test_name" == "full_test" ]]; then
  pytest_markers="integration and full"
elif [[ "$test_name" == "base_test" ]]; then
  pytest_markers="integration and base"
else
  echo "Only base and full integration tests supported"
  echo "call with one of:"
  echo "    interactive_test.sh base_test"
  echo "    interactive_test.sh full_test"
  exit 1
fi

logdir=$GEOIPS_OUTDIRS/logs/pytests/$test_name/`date -u +%Y%m%d`
mkdir -p $logdir
logfname=$logdir/`date -u +%Y%m%d.%H%M%S`_${test_name}.log

starting_output="""
`date -u`
Calling:
pytest -m \"$pytest_markers\" $repopath
Log output: $logfname
"""
echo "$starting_output"
echo "$starting_output" >> $logfname 2>&1

start_time=`date +%s`
pytest -m "$pytest_markers" $repopath >> $logfname 2>&1
retval=$?
end_time=`date +%s`

total_time=$((end_time-start_time))

# Standard copy/pasteable output for reference
final_output="""
Complete
geoips     $test_name
return     $retval
total time $total_time
`date -u`
"""

echo "$final_output"
echo "$final_output" >> $logfname 2>&1

exit $retval
