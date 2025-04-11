#!/bin/bash

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_smos/SM_OPER_MIR_SCNFSW_20240814T004732_20240814T022735_305_001_7.nc \
	--reader_name smos_winds_netcdf \
	--product_name unsectored \
	--output_formatter windspeed_awips2_formatter \

ss_retval=$?

exit $((ss_retval))
