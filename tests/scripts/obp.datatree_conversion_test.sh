#!/bin/bash
set -e

TEST_DATA="tests/outputs/abi.static.Infrared.netcdf_geoips/20200918.195020.goes-16.Infrared_latitude_longitude.test_goes16_eqc_10km_edge_night_20200918T1950Z.nc"

geoips run order_based test_datatree_conversions "$TEST_DATA"
