# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# This script calls pytest with standard arguments, and redirects output to
# $GEOIPS_OUTDIRS/logs/pytests.  Called as:
#     interactive_pytest.sh [interactive-pytest-command] [repopath] [explicit-pytest-args]

usage_message="""

interactive_pytest.sh will intelligently redirect output from
individual integration tests to individual log files.

Usage:

interactive_pytest.sh pre-defined-command repopath [explicit-pytest-args]

    * pre-defined-command  - REQUIRED shortcut to a specific combination of pytest markers and arguments (see below)
    * repopath             - REQUIRED path to repository you would like to run pytest on
    * explicit-pytest-args - OPTIONAL explicit additional arguments to pass to pytest

    Note ALL commands by default exclude the disabled marker.  You must explicitly
    request -m 'disabled' to get disabled tests to run.

    Call with one of the pre-defined-commands:

    all              - Run everything BUT disabled tests, with any specified arguments passed in.
    geoips-site      - only GeoIPS Site based tests (no real-time, pre-processing, or data ingest type tests)
    full-single-repo - Avoid having the same error cause tests to fail in multiple repositories.
    short            - short unit tests
    long             - long running unit tests
    required         - Tests NOT marked with optional
    optional         - Tests marked as optional

Example usage:

interactive_pytest.sh short         \$GEOIPS_PACKAGES_DIR
interactive_pytest.sh required      \$GEOIPS_PACKAGES_DIR
interactive_pytest.sh optional      \$GEOIPS_PACKAGES_DIR
interactive_pytest.sh all           \$GEOIPS_PACKAGES_DIR -m 'realtime'
interactive_pytest.sh all           \$GEOIPS_PACKAGES_DIR -m 'system'
interactive_pytest.sh all           \$GEOIPS_PACKAGES_DIR -m 'not system'
interactive_pytest.sh all           \$GEOIPS_PACKAGES_DIR/geoips -k amsr2.global
"""

repopath=`dirname $0`/../../
repopath=`realpath $repopath`
interactive_pytest_request="$1"
# Remove first argument
shift
repopath="$1"
# Remove second argument
shift
# Grab the rest of the arguments to pass through unchanged
# Just use $@ directly
# additional_args="$@"

if [[ "$repopath" == "" ]]; then
    echo "ERROR: Must pass at least 2 arguments."
    echo "$usage_message"
    exit 1
fi

# Make sure second argument is actually a directory if it exists.
if [[ ! -d "$repopath" ]]; then
    echo "ERROR: Second argument must be valid directory."
    echo "$usage_message"
    exit 1
fi

# Set full path to repo, and grab the .
if [[ "$repopath" != "" ]]; then
    repopath=`realpath $repopath`
fi

# Make sure we're calling on geoips repositories.
if [[ "$repopath" != "$GEOIPS_PACKAGES_DIR"* ]]; then
    echo "ERROR: Repo must live in GEOIPS_PACKAGES_DIR."
    echo "    $repopath"
    echo "$usage_message"
    exit 1
fi

# Make sure the interactive_pytest_request argument is expected.
if [[ "$interactive_pytest_request" != "geoips-site" &&
      "$interactive_pytest_request" != "required" &&
      "$interactive_pytest_request" != "optional" &&
      "$interactive_pytest_request" != "full-single-repo" &&
      "$interactive_pytest_request" != "short" &&
      "$interactive_pytest_request" != "long" &&
      "$interactive_pytest_request" != "all" ]]; then
    echo "ERROR: Limited pre-defined-commands supported"
    echo "$usage_message"
    exit 1
fi

# These should probably be markers, but for now just explicitly point to the test
# folders.
# I believe we do NOT want --capture=no and --tb=short for unit
# tests, but we DO want --capture=no and --tb=short for
# integration tests, since integration tests explicitly
# redirect all output to a file, but unit tests we
# only get the output pytest wants to give us.  If
# we continue to get spammed with large amounts of
# output on errors, we can readdress this for unit tests.

if [[ "$interactive_pytest_request" == "short" ]]; then
    pytest_marker_option="-m"
    pytest_marker_args="not disabled and not integration"
    pytest_keyword_option="-k"
    pytest_keyword_args="/unit_tests/"
    s_arg=""

elif [[ "$interactive_pytest_request" == "long" ]]; then
    pytest_marker_option="-m"
    pytest_marker_args="not disabled and not integration"
    pytest_keyword_option="-k"
    pytest_keyword_args="/unit_tests_long/"
    s_arg=""

elif [[ "$interactive_pytest_request" == "full-single-repo" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not disabled and full and not spans_multiple_packages"
    pytest_keyword_option=""
    pytest_keyword_args=""
    s_arg="--capture=no --tb=short"

elif [[ "$interactive_pytest_request" == "geoips-site" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not disabled and not system and not scheduler and not realtime and not scrubber and not database and not downloader and not external_preprocessing"
    pytest_keyword_option=""
    pytest_keyword_args=""
    s_arg="--capture=no --tb=short"

elif [[ "$interactive_pytest_request" == "required" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not optional and not disabled"
    pytest_keyword_option=""
    pytest_keyword_args=""
    s_arg="--capture=no --tb=short"

elif [[ "$interactive_pytest_request" == "optional" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="optional and not disabled"
    pytest_keyword_option=""
    pytest_keyword_args=""
    s_arg="--capture=no --tb=short"

elif [[ "$interactive_pytest_request" == "all" ]]; then
    testpath=$repopath
    # Need to pass -m because pytest.ini defaults to not disabled
    pytest_marker_option="-m"
    pytest_marker_args="not disabled"
    pytest_keyword_option=""
    pytest_keyword_args=""
    s_arg="--capture=no --tb=short"

else
    echo "ERROR: Must pass one of the supported interactive_pytest pre-defined commands"
    echo "$usage_message"
    exit 1
fi

reponame=`basename $repopath`
logdir=$GEOIPS_OUTDIRS/logs/pytests/interactive_pytest
integration_test_logdir=$GEOIPS_OUTDIRS/logs/pytests/integration
mkdir -p $logdir
mkdir -p $integration_test_logdir
logfname=$logdir/`date -u +%Y%m%d.%H%M%S`_${reponame}_${interactive_pytest_request}.log

currdir=$PWD
starting_output="""
`date -u`
env vars:
  GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS: $GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS
    * Unset to evaluate output file list, write to temporary output file list, and copy output files realtime repo.
    * export GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS=copy_files $GEOIPS_TESTDATA_DIR/realtime_outputs_$GEOIPS_SYSTEM_NAME/outputs
    * export GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS=write_output_file_list NA
    * export GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS=write_output_file_list_and_copy_files $GEOIPS_TESTDATA_DIR/realtime_outputs_$GEOIPS_SYSTEM_NAME/outputs
    * export GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS=run_file_list_comparison NA
    * export GEOIPS_REALTIME_TEST_OUTPUT_FILE_ARGS=run_file_list_comparison_and_copy_files $GEOIPS_TESTDATA_DIR/realtime_outputs_$GEOIPS_SYSTEM_NAME/outputs
  OUTPUT_CHECKER_THRESHOLD_IMAGE: $OUTPUT_CHECKER_THRESHOLD_IMAGE

`date -u`
Calling:
currdir=$PWD; cd $testpath

pytest $s_arg $pytest_marker_option "$pytest_marker_args" $pytest_keyword_option "$pytest_keyword_args" "$@"

cd $currdir
Log output: $logfname

To see all recent logs (since log filenames don't print out until AFTER each command is complete):
ls -lthr $integration_test_logdir/*
"""

echo "$starting_output"
echo "$starting_output" >> $logfname 2>&1

start_time=`date +%s`

# --rootdir $testpath does not seem to do the same as cd $testpath. Way fewer tests.
currdir=$PWD; cd $testpath
pytest $s_arg $pytest_marker_option "$pytest_marker_args" $pytest_keyword_option "$pytest_keyword_args" "$@" 2>&1 | tee -ai $logfname
retval=${PIPESTATUS[0]}

cd $currdir
end_time=`date +%s`

total_time=$((end_time-start_time))

# Standard copy/pasteable output for reference
final_output="""
Complete
$reponame  $interactive_pytest_request
args       "$@"
return     $retval
total time $total_time
`date -u`
user       $USER
Log file   $logfname
"""

echo "$final_output"
echo "$logfname"
echo "$final_output" >> $logfname 2>&1

# Must return appropriately!
exit $retval
