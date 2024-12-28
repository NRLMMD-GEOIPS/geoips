# # # This source code is protected under the license referenced at
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
    echo "    "`basename $0`" pytest_short $GEOIPS_PACKAGES_DIR/geoips"
    echo "    "`basename $0`" pytest_long $GEOIPS_PACKAGES_DIR/geoips"
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
elif [[ "$1" == "pytest_short" ]]; then
    test="pytest_short"
elif [[ "$1" == "pytest_long" ]]; then
    test="pytest_long"
elif [[ "$1" == "interfaces" ]]; then
    test="interfaces"
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
    echo "    pytest_short"
    echo "    pytest_long"
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
        echo flake8 --config $CONFIG_PATH/flake8 \
               $path
        flake8 --config $CONFIG_PATH/flake8 \
               $path
        flake8_retval=$?
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
if [[ "$test" == "pytest_short" || "$test" == "all" ]]; then
    echo ""
    echo "CALLING TEST:"

    if [[ "$GEOIPS_DISABLE_SHARED_CODE_CHECKS" == "True" ]]; then
        echo ""
        echo "GEOIPS_DISABLE_SHARED_CODE_CHECKS=True, skipping geoips pytests"
        pytest_short_geoips_retval="Not tested, GEOIPS_DISABLE_SHARED_CODE_CHECKS True"
    else
        # First test the geoips package pytests - these include pytests of any other
        # installed plugin packages, so always test geoips repo pytests.
        echo "pytest --cov=geoips -c $CONFIG_PATH/pytest.ini $geoips_path/tests/unit_tests"
        pytest --cov=geoips -c $CONFIG_PATH/pytest.ini $geoips_path/tests/unit_tests
        pytest_short_geoips_retval=$?
        retval=$((pytest_short_geoips_retval+retval))
    fi

    # Only test the current path if it is NOT geoips.  Don't test geoips twice.
    if [[ "$pkgname" != "geoips" && -d $path/tests/unit_tests ]]; then
        echo "pytest --cov=$pkgname -c $CONFIG_PATH/pytest.ini $path/tests/unit_tests"
        pytest --cov=$pkgname -c $CONFIG_PATH/pytest.ini $path/tests/unit_tests
        pytest_short_pkg_retval=$?

        # Return value of 5 indicates that no tests were run.
        # https://docs.pytest.org/en/7.1.x/reference/exit-codes.html
        # If no tests were run, still return 0.  Not all packages have
        # individual pytests defined, and we don't want a failure due to that.
        if [[ "$pytest_pkg_retval" == "5" ]]; then
            pytest_pkg_retval="No tests found"
        else
            # Add in the pkg pytest retval
            retval=$((pytest_short_pkg_retval+retval))
        fi
    elif [[ ! -d $path/tests/unit_tests ]]; then
        pytest_pkg_retval="No tests/unit_tests directory found"
    else
        pytest_pkg_retval="Not re-tested"
    fi
    echo "TEST COMPLETE pytest_short"
fi
# Do not include in "test" keyword - this takes a very long time to run
if [[ "$test" == "pytest_long" || "$test" == "all_test_data" ]]; then
    echo ""
    echo "CALLING TEST:"

    if [[ "$GEOIPS_DISABLE_SHARED_CODE_CHECKS" == "True" ]]; then
        echo ""
        echo "GEOIPS_DISABLE_SHARED_CODE_CHECKS=True, skipping geoips pytests"
        pytest_long_geoips_retval="Not tested, GEOIPS_DISABLE_SHARED_CODE_CHECKS True"
    else
        # First test the geoips package pytests - these include pytests of any other
        # installed plugin packages, so always test geoips repo pytests.
        echo "pytest --cov=geoips -c $CONFIG_PATH/pytest.ini $geoips_path/tests/unit_tests_long"
        pytest --cov=geoips -c $CONFIG_PATH/pytest.ini $geoips_path/tests/unit_tests_long
        pytest_long_geoips_retval=$?
        retval=$((pytest_long_geoips_retval+retval))
    fi

    # Only test the current path if it is NOT geoips.  Don't test geoips twice.
    if [[ "$pkgname" != "geoips" && -d "$path/tests/unit_tests_long" ]]; then
        echo "pytest --cov=$pkgname -c $CONFIG_PATH/pytest.ini $path/tests/unit_tests_long"
        pytest --cov=$pkgname -c $CONFIG_PATH/pytest.ini $path/tests/unit_tests_long
        pytest_long_pkg_retval=$?

        # Return value of 5 indicates that no tests were run.
        # https://docs.pytest.org/en/7.1.x/reference/exit-codes.html
        # If no tests were run, still return 0.  Not all packages have
        # individual pytests defined, and we don't want a failure due to that.
        if [[ "$pytest_pkg_retval" == "5" ]]; then
            pytest_pkg_retval="No tests found"
        else
            # Add in the pkg pytest retval
            retval=$((pytest_long_pkg_retval+retval))
        fi
    elif [[ ! -d $path/tests/unit_tests_long ]]; then
        pytest_pkg_retval="No tests/unit_tests_long directory found"
    else
        pytest_pkg_retval="Not re-tested"
    fi
    echo "TEST COMPLETE pytest_long"
fi
if [[ "$test" == "interfaces" || "$test" == "all" ]]; then
    if [[ "$GEOIPS_DISABLE_SHARED_CODE_CHECKS" == "True" ]]; then
        echo ""
        echo "GEOIPS_DISABLE_SHARED_CODE_CHECKS=True, skipping test_interfaces"
        interfaces_retval="Not tested, GEOIPS_DISABLE_SHARED_CODE_CHECKS True"
    else
        echo ""
        echo "CALLING TEST interfaces:"
        echo "python $geoips_path/tests/utils/test_interfaces.py"
        python $geoips_path/tests/utils/test_interfaces.py
        interfaces_retval=$?
        echo "TEST COMPLETE interfaces"
        retval=$((interfaces_retval+retval))
    fi
fi
echo ""
echo "$0 $@"
echo ""
echo "  black return: $black_retval"
echo "  flake8 return: $flake8_retval"
echo "  bandit return: $bandit_retval"
echo "  pytest_short geoips return: $pytest_short_geoips_retval"
echo "  pytest_long geoips return: $pytest_long_geoips_retval"
echo "  pytest_short $pkgname return: $pytest_short_pkg_retval"
echo "  pytest_long $pkgname return: $pytest_long_pkg_retval"
echo "  interfaces return: $interfaces_retval"
echo ""
echo "Overall `basename $0` return: $retval"
exit $retval
