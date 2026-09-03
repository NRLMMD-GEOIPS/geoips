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

path="$( cd $2 && pwd)"
geoips_path="$( cd "$( dirname "$0")/../../" && pwd)"
extra_args=$3
lint_dir="$geoips_path/tests/lint"

retval=0
black_retval="Not run"
flake8_retval="Not run"
bandit_retval="Not run"
doc8_retval="Not run"

run_pytest() {
    pytest -q --tb=short "$@"
    return $?
}

if [[ "$test" == "black" || "$test" == "all" ]]; then
    echo ""
    echo "CALLING TEST:"
    echo "black --check --diff --config $geoips_path/.config/black $path"
    echo "pytest -q --tb=short -m black $lint_dir/ --lint-path $path"
    run_pytest -m black "$lint_dir/" --lint-path "$path"
    black_retval=$?
    echo "TEST COMPLETE black"
    retval=$((black_retval+retval))
fi

if [[ "$test" == "flake8" || "$test" == "all" ]]; then
    if [[ "$extra_args" == *"flake8_docstring_only"* ]]; then
        docstring_flag="--flake8-docstring-only"
    else
        docstring_flag=""
    fi
    if [[ "$extra_args" == *"no_flake8"* ]]; then
        echo ""
        echo "no_flake8 requested, skipping flake8"
        flake8_retval="Not tested, flake8 not requested"
    else
        echo "CALLING TEST:"
        echo "flake8 $path"
        echo "pytest -q --tb=short -m flake8 $lint_dir/ --lint-path $path $docstring_flag"
        run_pytest -m flake8 "$lint_dir/" --lint-path "$path" $docstring_flag
        flake8_retval=$?
        echo "TEST COMPLETE flake8"
        retval=$((flake8_retval+retval))
    fi
fi

if [[ "$test" == "bandit" || "$test" == "all" ]]; then
    echo ""
    echo "CALLING TEST:"
    echo "bandit -ll -r $path"
    echo "pytest -q --tb=short -m bandit $lint_dir/ --lint-path $path"
    run_pytest -m bandit "$lint_dir/" --lint-path "$path"
    bandit_retval=$?
    echo "TEST COMPLETE bandit"
    retval=$((bandit_retval+retval))
fi

if [[ "$test" == "doc8" ]]; then
    echo ""
    echo "CALLING TEST:"
    echo "doc8 --max-line-length=120 $path/docs/source"
    echo "pytest -q --tb=short -m doc8 $lint_dir/ --lint-path $path"
    run_pytest -m doc8 "$lint_dir/" --lint-path "$path"
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
