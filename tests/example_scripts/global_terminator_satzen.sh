# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

###############################
## Infrared-Day-Only and Infrared-Night-Only Products

# MSG-1 IODC

if [[ "$1" == "" ]]; then
  echo "Usage:"
  echo "To run a specific dataset:"
  echo "    $0 [reader_name] [product-name-base] [files]"
  echo ""
  echo "To run pre-set examples for each data type:"
  echo "    $0 all"
  echo ""
  echo "product-name-base: specifies prefix used in product names found in satzen procflow config."
  echo "Environment variable GLOBAL_SATZEN_PRODUCT_BASE=$2, and that env var is used in the procflow config as follows:"
  echo "    \${GLOBAL_SATZEN_PRODUCT_BASE}-Day-Night"
  echo "    \${GLOBAL_SATZEN_PRODUCT_BASE}-Day-Only"
  echo "    \${GLOBAL_SATZEN_PRODUCT_BASE}-Night-Only"
  echo ""
  echo "Note all satellites have Test-Infrared product prefix defined, and that is what is used for 'all' option."
  echo "Additional Test-Infrared, etc products can be defined for use with datasets that may not have the typical Infrared channel"
  echo "e.g. GLOBAL_SATZEN_PRODUCT_BASE=Test-Infrared-ABI-B13 will support Test-Infrared-ABI-B13-Day-Night, etc products using B13 rather than B14"
  echo ""
  exit 1
fi

# If we pass in arguments, just run the one command
if [[ "$1" != "" && "$2" != "" && "$3" != "" ]]; then
  reader="$1" 
  export GLOBAL_SATZEN_PRODUCT_BASE="$2"
  fnames="$3"
  echo geoips run config_based \
    $fnames \
    --reader_name $reader \
    --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
  geoips run config_based \
    $fnames \
    --reader_name $reader \
    --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
  retval=$?

  ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/abi/*
  ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ahi/*
  ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ami/*
  ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/seviri/*
  ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/fci/*

  mkdir -p $GEOIPS_OUTDIRS/example_test_imagery_outputs
  cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/abi/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
  cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ahi/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
  cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ami/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
  cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/seviri/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
  cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/fci/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
  exit $retval
fi

export GLOBAL_SATZEN_PRODUCT_BASE="Test-Infrared"

final_retval=0
# This is WV 6.2um only
# $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20231211/0800/*MSG2_IODC* \
# Masking off, need to fix.
geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/*MSG1_IODC* \
  --reader_name seviri_hrit \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval_msg1=$?
final_retval=$((final_retval+retval_msg1))

# GEOKOMPSAT-2A

# Masking off, need to fix.
geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_ami/data/20231208_0300_daytime/gk2a_ami_le1b_*.nc \
  --reader_name ami_netcdf \
  --resampled_read \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval_gk2a=$?
final_retval=$((final_retval+retval_gk2a))

# MTG-1

# resampled_read does not work for FCI !
geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_fci/data/mt1_fdhsi_20240113_1150/* \
  --reader_name fci_netcdf \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval_mt1=$?
final_retval=$((final_retval+retval_mt1))

# Himawari-8

geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_ahi/data/20200405_0000/HS_H08* \
  --reader_name ahi_hsd \
  --resampled_read \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval_h8=$?
final_retval=$((final_retval+retval_h8))

# GOES-16

geoips run config_based \
  ${GEOIPS_TESTDATA_DIR}/test_data_abi/data/goes16_20200918_1950/OR_ABI-L1b*_G16_*.nc \
  --reader_name abi_netcdf \
  --resampled_read \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval_g16=$?
final_retval=$((final_retval+retval_g16))

# GOES-17

geoips run config_based \
  $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes17_20210718_0150/OR_ABI-L1b*_G17_*.nc \
  --reader_name abi_netcdf \
  --resampled_read \
  --output_config $GEOIPS_PACKAGES_DIR/geoips/tests/example_scripts/satzen.yaml
retval_g17=$?
final_retval=$((final_retval+retval_g17))

ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/abi/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ahi/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ami/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/seviri/*
ls -l $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/fci/*

mkdir -p $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/abi/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ahi/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/ami/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/seviri/* $GEOIPS_OUTDIRS/example_test_imagery_outputs
cp -pv $GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x/Test-Infrared-*-*/fci/* $GEOIPS_OUTDIRS/example_test_imagery_outputs

echo "g16: $retval_g16"
echo "g17: $retval_g17"
echo "gk2a: $retval_gk2a"
echo "mt1: $retval_mt1"
echo "msg1: $retval_msg1"
echo "h8: $retval_h8"
echo "Final retval: $final_retval"
