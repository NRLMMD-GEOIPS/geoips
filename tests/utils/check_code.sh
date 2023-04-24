# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

#!/bin/sh

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
    echo "    "`basename $0`" all $GEOIPS_PACKAGES_DIR/geoips"
    echo ""
    echo "Returns 0 if all checks pass"
    echo ""
    echo "Supported extra arguments:"
    echo "    flake8_docstring_only"
    echo ""
    exit 1
fi

if [[ "$1" == "black" ]]; then
    test="black"
elif [[ "$1" == "flake8" ]]; then
    test="flake8"
elif [[ "$1" == "bandit" ]]; then
    test="bandit"
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
    echo ""
    exit 1
fi

path=$2

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
    echo "black --check --extend-exclude /version.py $path"
    black --check --extend-exclude /version.py $path
    black_retval=$?
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
    echo flake8 --max-line-length=88 \
           $select_string \
           --ignore=E203,W503 \
           --extend-exclude="version.py" \
           --docstring-convention=numpy \
           --rst-roles=class,func,ref \
           --rst-directives=envvar,exception \
           --rst-substitutions=version \
           $path
    flake8 --max-line-length=88 \
           $select_string \
           --ignore=E203,W503 \
           --extend-exclude="version.py" \
           --docstring-convention=numpy \
           --rst-roles=class,func,ref \
           --rst-directives=envvar,exception \
           --rst-substitutions=version \
           $path
    flake8_retval=$?
    retval=$((flake8_retval+retval))
fi
if [[ "$test" == "bandit" || "$test" == "all" ]]; then
    echo "bandit -ll -r path"
    bandit -ll -r $path
    bandit_retval=$?
    retval=$((bandit_retval+retval))
fi
echo ""
echo "$0 $@"
echo ""
echo "  black return: $black_retval"
echo "  flake8 return: $flake8_retval"
echo "  bandit return: $bandit_retval"
echo ""
echo "Overall `basename $0` return: $retval"
exit $retval
