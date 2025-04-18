# This script calls pytest with standard arguments, and redirects output to
# $GEOIPS_OUTDIRS/logs/pytests.  Called as either:
#     interactive_test.sh base_test
#         # CALLS pytest -m "integration and base" $repopath
#     interactive_test.sh full_test
#         # CALLS pytest -m "integration and full" $repopath

repopath=`dirname $0`/../../
repopath=`realpath $repopath`
pytest_marker="$1"

usage_message="""
call with one of:
    interactive_pytest.sh integration [repopath]
    interactive_pytest.sh base [repopath]
    interactive_pytest.sh full [repopath]
    interactive_pytest.sh extra [repopath]
    interactive_pytest.sh system [repopath]
    interactive_pytest.sh realtime [repopath]
    interactive_pytest.sh short [repopath]
    interactive_pytest.sh long [repopath]
"""

if [[ "$2" == "" ]]; then
    echo "Must pass 2 arguments."
    echo "$usage_message"
    exit 1
fi

# Make sure second argument is actually a directory if it exists.
if [[ ! -d "$2" ]]; then
    echo "Second argument must be valid directory."
    echo "$usage_message"
    exit 1
fi

# Set full path to repo, and grab the .
if [[ "$2" != "" ]]; then
    repopath=`realpath $2`
fi

# Make sure we're calling on geoips repositories.
if [[ "$repopath" != "$GEOIPS_PACKAGES_DIR"* ]]; then
    echo "Repo must live in GEOIPS_PACKAGES_DIR."
    echo "    $repopath"
    echo "$usage_message"
    exit 1
fi

# Make sure the pytest_marker argument is expected.
if [[ "$pytest_marker" != "integration" &&
      "$pytest_marker" != "full" &&
      "$pytest_marker" != "base" &&
      "$pytest_marker" != "extra" &&
      "$pytest_marker" != "system" &&
      "$pytest_marker" != "realtime" &&
      "$pytest_marker" != "short" &&
      "$pytest_marker" != "long" ]]; then
    echo "Limited pytests supported"
    echo "$usage_message"
    exit 1
fi

# These should probably be markers, but for now just explicitly point to the test
# folders.
if [[ "$pytest_marker" == "short" ]]; then
    testpath=$repopath/tests/unit_tests
    pytest_marker_arg=""
elif [[ "$pytest_marker" == "long" ]]; then
    testpath=$repopath/tests/unit_tests_long
    pytest_marker_arg=""
else
    testpath=$repopath
    pytest_marker_arg="-m $pytest_marker"
fi

reponame=`basename $repopath`
logdir=$GEOIPS_OUTDIRS/logs/pytests/
mkdir -p $logdir
logfname=$logdir/`date -u +%Y%m%d.%H%M%S`_${reponame}_${pytest_marker}.log

starting_output="""
`date -u`
Calling:
pytest $pytest_marker_arg $testpath
Log output: $logfname
"""

echo "$starting_output"
echo "$starting_output" >> $logfname 2>&1

start_time=`date +%s`
pytest "$pytest_marker_arg" $testpath 2>&1 | tee -ai $logfname
retval=${PIPESTATUS[0]}
end_time=`date +%s`

total_time=$((end_time-start_time))

# Standard copy/pasteable output for reference
final_output="""
Complete
$reponame  $pytest_marker
return     $retval
total time $total_time
`date -u`
"""

echo "$final_output"
echo "$logfname"
echo "$final_output" >> $logfname 2>&1

# Must return appropriately!
exit $retval
