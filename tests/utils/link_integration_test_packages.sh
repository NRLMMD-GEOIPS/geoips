#!/bin/sh

# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#######################################################################################
### NOTE we can NOT link the pytest packages any longer, because pydantic validation
### will fail due to the current file location not matching the "registered"
### location.  E.g. we CAN'T have both a geoips_packages and
### geoips_packages/pytest_packages for pydantic validation.  A bunch of pydantic
### unit tests will fail.
### Thus - we just need to link pytest.ini to geoips_packages, then we need to ensure
### all python packages that live in geoips_packages are valid and will not cause pytest
### to fail (e.g., if there are non-pytest formatted scripts named test_...py anywhere
### within geoips_packages, pytest will just not run at all).
#######################################################################################

# PYTEST_PACKAGES_DIR=$GEOIPS_PACKAGES_DIR/pytest_packages
# echo "Linking all packages with integration tests to pytest_packages"
# echo ""
# echo "mkdir -p $PYTEST_PACKAGES_DIR"
# mkdir -p $PYTEST_PACKAGES_DIR
# echo ""
# for dirname in $GEOIPS_PACKAGES_DIR/*/tests/integration_tests; do
#     # Grab the package name, the 3rd from the last directory.
#     package_name=`echo $dirname |  rev | cut -f 3 -d / | rev`
#     # Link package name into pytest_packages
#     echo "ln -sfv $GEOIPS_PACKAGES_DIR/$package_name ${PYTEST_PACKAGES_DIR}"
#     ln -sfv $GEOIPS_PACKAGES_DIR/$package_name ${PYTEST_PACKAGES_DIR}
# done
#
# echo ""
# # We need the geoips pytest.ini
# echo "ln -sfv $GEOIPS_PACKAGES_DIR/geoips/pytest.ini $PYTEST_PACKAGES_DIR/"
# ln -sfv $GEOIPS_PACKAGES_DIR/geoips/pytest.ini $PYTEST_PACKAGES_DIR/
#
# echo ""
# # Remove the pytest_packages link... So we don't run everything infinite times...
# rm -fv $PYTEST_PACKAGES_DIR/pytest_packages
#
# echo ""
# # Link this linking script into pytest_packages, for good measure.
# # DON'T force or it will overwrite the original..
# echo "ln -sv `realpath $0` $PYTEST_PACKAGES_DIR/"
# ln -sv `realpath $0` $PYTEST_PACKAGES_DIR/
#
# echo ""
# echo "This ensures only packages with supported pytest-based integration tests are included in the exhaustive system test"
# echo "Call all pytest-based integration tests with:"
# echo "***************"
# echo "$GEOIPS_PACKAGES_DIR/geoips/tests/utils/interactive_pytest.sh integration $PYTEST_PACKAGES_DIR"
# echo "***************"

# Now we just want to link pytest.ini to $GEOIPS_PACKAGES_DIR, we need to clean up
# all the plugin packages so they do not cause pytest to error before even starting. 
echo "ln -sfv $GEOIPS_PACKAGES_DIR/geoips/pytest.ini $GEOIPS_PACKAGES_DIR/"
ln -sfv $GEOIPS_PACKAGES_DIR/geoips/pytest.ini $GEOIPS_PACKAGES_DIR/
