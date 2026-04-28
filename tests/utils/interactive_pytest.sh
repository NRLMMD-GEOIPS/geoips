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

# If the user did not specifically request suppression or no suppression of failed
# log outputs, then do not suppress the failed log outputs by default.
# This ensures all log outputs end up in a single file for easy querying.
# Set to true for a cleaner interactive log output.
if [[ "$GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS" == "" ]]; then
    export GEOIPS_TEST_SUPPRESS_PYTEST_FAILED_LOG_CONTENTS="False"
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
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not disabled"
    s_arg=""
    test_dirname="tests/unit_tests/"

elif [[ "$interactive_pytest_request" == "long" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not integration and not disabled and not optional"
    s_arg=""
    test_dirname="tests/unit_tests_long/"

elif [[ "$interactive_pytest_request" == "full-single-repo" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not disabled and full and not spans_multiple_packages"
    s_arg="--capture=no --tb=short"
    test_dirname=""

elif [[ "$interactive_pytest_request" == "geoips-site" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not disabled and not system and not scheduler and not realtime and not scrubber and not database and not downloader and not external_preprocessing"
    s_arg="--capture=no --tb=short"
    test_dirname=""

elif [[ "$interactive_pytest_request" == "required" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="not optional and not disabled"
    s_arg="--capture=no --tb=short"
    test_dirname=""

elif [[ "$interactive_pytest_request" == "optional" ]]; then
    testpath=$repopath
    pytest_marker_option="-m"
    pytest_marker_args="optional and not disabled"
    s_arg="--capture=no --tb=short"
    test_dirname=""

elif [[ "$interactive_pytest_request" == "all" ]]; then
    testpath=$repopath
    s_arg="--capture=no --tb=short"
else
    echo "ERROR: Must pass one of the supported interactive_pytest pre-defined commands"
    echo "$usage_message"
    exit 1
fi

if [[ "$interactive_pytest_request" != "all" && "$pytest_marker_args" == "" ]]; then
    echo "ERROR: Must not implement interactive_pytest function without pytest_marker_args."
    echo "Set to not disabled or something"
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
Calling:
currdir=$PWD
cd $testpath
pytest $test_dirname $s_arg $pytest_marker_option "$pytest_marker_args" "$@"
cd $currdir
Log output: $logfname

To see all recent logs (since log filenames don't print out until AFTER each command is complete):
ls -lthr $integration_test_logdir/*
"""

echo "$starting_output"
echo "$starting_output" >> $logfname 2>&1

start_time=`date +%s`

# --rootdir $testpath does not seem to do the same as cd $testpath. Way fewer tests.
# Also note you must be very careful about passing empty strings to pytest, if any of
# the arguments that get passed in with "" are empty variables, then "" gets passed
# into pytest as an actual directory argument, resulting in pytest running on ALL
# files and directories at the top level regardless of what you pass in as test_dirname.
# So ensure if this script is updated, we never include empty variables in "".
currdir=$PWD; cd $testpath; pwd
if [[ "$interactive_pytest_request" == "all" ]]; then
    pytest $test_dirname $s_arg "$@" 2>&1 | tee -ai $logfname
    retval=${PIPESTATUS[0]}
elif [[ "$@" == "" ]]; then
    pytest $test_dirname $s_arg $pytest_marker_option "$pytest_marker_args" 2>&1 | tee -ai $logfname
    retval=${PIPESTATUS[0]}
else
    pytest $test_dirname $s_arg $pytest_marker_option "$pytest_marker_args" "$@" 2>&1 | tee -ai $logfname
    retval=${PIPESTATUS[0]}
fi

cd $currdir
end_time=`date +%s`

total_time=$((end_time-start_time))

# Standard copy/pasteable output for reference
final_output="""
Complete
`grep "PASSED LOG FILE: " $logfname`
`grep "FAILED LOG FILE: " $logfname`
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
