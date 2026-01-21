# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

echo "$0 $@"

if [[ "$1" == "" || "$2" == "" ]]; then
    echo ""
    echo "Usage: "
    echo "$0 <executable> <path> [<extra supported arguments>]"
    echo ""
    echo "ie:"
    echo "    "`basename $0`" black $GEOIPS_PACKAGES_DIR/geoips"
    echo "    "`basename $0`" flake8 $GEOIPS_PACKAGES_DIR/geoips"
    echo "    "`basename $0`" bandit $GEOIPS_PACKAGES_DIR/geoips"
    echo "    "`basename $0`" doc8 $GEOIPS_PACKAGES_DIR/geoips"
    echo "    "`basename $0`" all $GEOIPS_PACKAGES_DIR/geoips"
    echo ""
    echo "Returns 0 if all checks pass"
    echo ""
    echo "Supported extra arguments:"
    echo "    flake8_docstring_only"
    echo "    no_flake8"
    echo ""
    exit 1
fi

if [[ "$1" == "black" ]]; then
    test="black"
elif [[ "$1" == "flake8" ]]; then
    test="flake8"
elif [[ "$1" == "bandit" ]]; then
    test="bandit"
elif [[ "$1" == "doc8" ]]; then
    test="doc8"
elif [[ "$1" == "all" ]]; then
    test="all"
else
    echo ""
    echo "Unsupported code checker: $1"
    echo ""
    echo "Supported checkers:"
    echo "    black"
    echo "    flake8"
    echo "    bandit"
    echo "    doc8"
    echo ""
    exit 1
fi

# Get the full path, not just relative
path="$( cd $2 && pwd)"
geoips_path="$( cd "$( dirname "$0")/../../" && pwd)"
pkgname=`basename $path`
# Get the full path to the geoips .config directory, pwd removes the relative paths
CONFIG_PATH="$( cd "$( dirname "$0")/../../.config" && pwd)"
extra_args=$3

retval=0
args=""

# These are the actual supported calls to black, flake8, and bandit.
# Don't allow too many options, to ensure we have consistent application / enforcement.
if [[ "$test" == "black" || "$test" == "all" ]]; then
    # black excludes regex for file names - so include leading "/" so it matches
    # EXACTLY the file named version.py
    # NOTE this will exclude ANY file named version.py ANYWHERE in the code base.
    # This will probably be fine, but if we determine in the future that we
    # really want to be able to name a file "version.py" and want it checked
    # for compliance, we will need to rethink.
    echo ""
    # NOTE: black just checks for substrings in the string of the full path -
    #       so include / around dirs to make sure we only match the dirs.
    #       Also, do NOT include "*" in the path (since it is just looking for
    #       substrings directly)
    echo "CALLING TEST:"
    echo "black --config $CONFIG_PATH/black $path"
    # Note - black does not have a default single-file config (default for
    # pyproject.toml section, but no single-file default).  Thus - store the
    # black condig in $GEOIPS/.config/black, and use that for appropriate settings
    # across all repos.
    black --config $CONFIG_PATH/black $path
    black_retval=$?
    echo "TEST COMPLETE black"
    retval=$((black_retval+retval))
fi
if [[ "$test" == "flake8" || "$test" == "all" ]]; then
    if [[ "$extra_args" == *"flake8_docstring_only"* ]]; then
        # RST is numpy docstring formatting
        # D100/103 missing docstring in module/function
        # D201/202 no blank lines before/after docstring
        # D401 Imperative mood in docstring
        select_string="--select=RST,D"
    else
        select_string=""
    fi
    # flake8 excludes exact file name - so no leading "/"
    # NOTE this will exclude ANY file named version.py ANYWHERE in the code base.
    # This will probably be fine, but if we determine in the future that we
    # really want to be able to name a file "version.py" and want it checked
    # for compliance, we will need to rethink.

    # W503 and E203 conflict with black, so ignore.
    # W503 is line break before binary operator
    # E203 is white space before :
    # E712 is "== False" usage - causes problems with np.ma.where commands, if you
    #      change "== False" to "is False" it will NOT work.
    if [[ "$extra_args" == *"no_flake8"* ]]; then
        echo ""
        echo "no_flake8 requested, skipping flake8"
        flake8_retval="Not tested, flake8 not requested"
    else
        # NOTE: flake8 matches subdirectories or filenames exactly.
        #       So, do not include "/" in the extend-exclude, since it is
        #       not attempting to match the full string path, but each individual
        #       subdirectory or file.
        echo "CALLING TEST:"
        # Do not pass flake8 config - assume default exists.
        echo flake8 $path
        # Note - flake8 picks up .flake8 in your CWD, not in the path you are running
        # flake8 on.  Thus, cd to $path before running flake8 to ensure we pick up
        # the appropriate flake8 config for the current repository. Alternatively,
        # we could just pass in the config file directly, but this ensures we are
        # testing the default behaviour of flake8.
        start_dir=$PWD
        cd $path
        flake8 $path
        flake8_retval=$?
        # Switch back to where we were, just in case.
        cd $start_dir
        echo "TEST COMPLETE flake8"
        retval=$((flake8_retval+retval))
    fi
fi
if [[ "$test" == "bandit" || "$test" == "all" ]]; then
    echo ""
    echo "CALLING TEST:"
    echo "bandit -ll -r path"
    bandit -ll -r $path
    bandit_retval=$?
    echo "TEST COMPLETE bandit"
    retval=$((bandit_retval+retval))
fi
if [[ "$test" == "doc8" || "$test" == "all" ]]; then
    echo ""
    echo "CALLING TEST:"
    echo "doc8 --max-line-length=120 $path/docs/source"
    doc8 --max-line-length=120 $path/docs/source
    doc8_retval=$?
    echo "TEST COMPLETE doc8"
    retval=$((doc8_retval+retval))
fi
echo ""
echo "$0 $@"
echo ""
echo "  black return: $black_retval"
echo "  flake8 return: $flake8_retval"
echo "  bandit return: $bandit_retval"
echo "  doc8 return: $doc8_retval"
echo ""
echo "Overall `basename $0` return: $retval"
exit $retval
