# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

###############################
## Script to evaluate contents of individual geostationary datasets by plotting
## a single channel (for efficiency) reprojected to a global grid, and outputting
## annotated imagery outputs for quick evaluation of the requested dataset.
##
## Produces:
## * Test-Day-Only product to identify which portion of the data contains daytime data.
## * Test-Night-Only product to identify which portion of the data contains night data.
## * Test-Day-Night product to display the full extent of the dataset.
## * Satellite zenith cutoff of None to show the full extent of the dataset.
## * Satellite zenith cutoff of 70 degrees for reference where valid data exists.

if [[ "$1" == "" && "$2" == "" && "$3" == "" ]]; then
  echo "Usage:"
  echo "To run a specific dataset:"
  echo "    $0 [reader_name] [product-name-base] [files]"
  echo ""
  echo "product-name-base: specifies prefix used in product names found in satzen procflow config."
  echo "Environment variable GLOBAL_SATZEN_PRODUCT_BASE=$2, and that env var is used in the procflow config as follows:"
  echo "    \${GLOBAL_SATZEN_PRODUCT_BASE}-Day-Night"
  echo "    \${GLOBAL_SATZEN_PRODUCT_BASE}-Day-Only"
  echo "    \${GLOBAL_SATZEN_PRODUCT_BASE}-Night-Only"
  echo ""
  echo "Test- products are used exclusively for efficient test processing and evaluation."
  echo "If a test product does not exist for a given dataset, you can add additional plugins as needed for additional channels."
  echo "Current Test products are defined in:"
  echo "   geoips/plugins/yaml/products/integration_tests/Test-Day-Night.yaml"
  echo "   geoips/plugins/yaml/products/integration_tests/Test-Day-Only.yaml"
  echo "   geoips/plugins/yaml/products/integration_tests/Test-Night-Only.yaml"
  echo ""
  echo "Currently defined Test-Day-Night products include (same defined for Day-Only and Night-Only as well):"
  echo "  * Test-ABI-B14-Day-Night (standard infrared channel)"
  echo "  * Test-ABI-B13-Day-Night (geocolor Infrared channel)"
  echo "  * Test-AHI-B13-Day-Night (standard infrared channel)"
  echo "  * Test-AMI-11p2-Day-Night (standard infrared channel)"
  echo "  * Test-FCI-B14-Day-Night (standard infrared channel)"
  echo "  * Test-SEVIRI-B9-Day-Night (standard infrared channel)"
  echo ""
  exit 1
fi

reader="$1" 
export GLOBAL_SATZEN_PRODUCT_BASE="$2"
fnames="$3"
echo geoips run config_based \
  $fnames \
  --reader_name $reader \
  --resampled_read
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
geoips run config_based \
  $fnames \
  --reader_name $reader \
  --resampled_read \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval=$?

mkdir -p $GEOIPS_OUTDIRS/example_test_imagery_outputs

ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/abi/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/ahi/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/ami/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/seviri/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/fci/*

cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/abi/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/ahi/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/ami/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/seviri/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/${GLOBAL_SATZEN_PRODUCT_BASE}-*-*/fci/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
exit $retval
