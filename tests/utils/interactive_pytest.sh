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
pytest_marker="$1"

usage_message="""
call with one of:
    # Run ALL integration tests!
    interactive_pytest.sh integration [repopath]

    # Run all tests for complete open source site testing
    interactive_pytest.sh site-nrlmmd-geoips [repopath]

    # Just test single plugins functionality.
    interactive_pytest.sh base [repopath]
    interactive_pytest.sh full [repopath]

    # NO tests that touch multiple packages
    # Avoid having the same error cause multiple tests to fail.
    #       -m 'full and not spans_multiple_packages'
    interactive_pytest.sh full_single_repo [repopath]

    # Grab all the tests we missed in full_single_repo
    #       -m 'spans_multiple_packages'
    interactive_pytest.sh spans_multiple_packages [repopath]

    # Run all System implementation tests
    interactive_pytest.sh realtime [repopath]
    interactive_pytest.sh scheduler [repopath]
    interactive_pytest.sh database [repopath]
    interactive_pytest.sh scrubber [repopath]
    interactive_pytest.sh downloader [repopath]
    interactive_pytest.sh external_preprocessing [repopath]

    # pytest unit tests
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
      "$pytest_marker" != "site-nrlmmd-geoips" &&
      "$pytest_marker" != "full" &&
      "$pytest_marker" != "base" &&
      "$pytest_marker" != "spans_multiple_packages" &&
      "$pytest_marker" != "full_single_repo" &&
      "$pytest_marker" != "realtime" &&
      "$pytest_marker" != "scheduler" &&
      "$pytest_marker" != "database" &&
      "$pytest_marker" != "scrubber" &&
      "$pytest_marker" != "downloader" &&
      "$pytest_marker" != "external_preprocessing" &&
      "$pytest_marker" != "short" &&
      "$pytest_marker" != "long" ]]; then
    echo "Limited pytests supported"
    echo "$usage_message"
    exit 1
fi

# These should probably be markers, but for now just explicitly point to the test
# folders.
s_arg=""
if [[ "$pytest_marker" == "short" ]]; then
    if [[ -d $repopath/tests/unit_tests ]]; then
        # This is for testing a single repository
        testpath=$repopath/tests/unit_tests
    else
        # This is for testing the full geoips_packages folder
        testpath=$repopath/*/tests/unit_tests
    fi
    pytest_marker_arg=""
elif [[ "$pytest_marker" == "long" ]]; then
    if [[ -d $repopath/tests/unit_tests_long ]]; then
        # This is for testing a single repository
        testpath=$repopath/tests/unit_tests_long
    else
        # This is for testing the full geoips_packages folder
        testpath=$repopath/*/tests/unit_tests_long
    fi
    pytest_marker_arg=""
elif [[ "$pytest_marker" == "full_single_repo" ]]; then
    testpath=$repopath
    pytest_marker_arg="full and not spans_multiple_packages"
    s_arg="-s"
elif [[ "$pytest_marker" == "site-nrlmmd-geoips" ]]; then
    testpath=$repopath
    pytest_marker_arg="integration and not limited_test_dataset_availability or not integration"
    s_arg="-s"
else
    testpath=$repopath
    pytest_marker_arg=$pytest_marker
    s_arg="-s"
fi

reponame=`basename $repopath`
logdir=$GEOIPS_OUTDIRS/logs/pytests/
mkdir -p $logdir
logfname=$logdir/`date -u +%Y%m%d.%H%M%S`_${reponame}_${pytest_marker}.log

starting_output="""
`date -u`
env vars:
  GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS: $GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS
    * Unset to evaluate outputs.
    * write_output_file_list NA
    * run_file_list_comparison NA
  OUTPUT_CHECKER_THRESHOLD_IMAGE: $OUTPUT_CHECKER_THRESHOLD_IMAGE

`date -u`
Calling:
pytest $s_arg -m "$pytest_marker_arg" $testpath
Log output: $logfname
"""

echo "$starting_output"
echo "$starting_output" >> $logfname 2>&1

start_time=`date +%s`
pytest $s_arg -m "$pytest_marker_arg" $testpath 2>&1 | tee -ai $logfname
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
