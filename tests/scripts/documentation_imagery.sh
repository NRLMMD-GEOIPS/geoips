# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

#!/bin/bash

#######################################################################################################################
### Exact calls for producing all imagery contained in "available_functionality.rst" documentation
### This script:
###     * runs the commands,
###     * copies the resulting imagery into the available_functionality image directory
###     * Checks that the return from both the geoips run single_source and cp commands were 0
###         * exit entire script with return code 1 upon any non-zero return code
#######################################################################################################################


retval=0
avfunc=$GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality
globdir=$GEOIPS_OUTDIRS/preprocessed/annotated_imagery/Global-x-x/x-x-x

check_returns() {
    echo "AFTER COPY $2"
    echo "retval: $1"
    if [[ "$1" != "0" ]]; then
        echo "FAILED non-zero return value, quitting."
        exit 1
    fi
}

####################################################################
# 1.4.2 unprojected_imagery
####################################################################

$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/seviri.WV-Upper.unprojected_image.sh
curr_retval=$?
echo ""
output_image=$GEOIPS_OUTDIRS/preprocessed/annotated_imagery/x-x-x/x-x-x/WV-Upper/seviri/20200404.080000.msg-1.seviri.WV-Upper.self_register.69p07.nesdisstar.10p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $avfunc/*seviri*
check_returns $retval $output_image

####################################################################
# 1.4.2 unprojected_imagery
####################################################################

$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/modis.Infrared.unprojected_image.sh
curr_retval=$?
echo ""
output_image=$GEOIPS_OUTDIRS/preprocessed/annotated_imagery/x-x-x/x-x-x/Infrared/modis/20210104.201500.aqua.modis.Infrared.self_register.100p00.nasa.3p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*modis*
check_returns $retval $output_image

####################################################################
# 1.3.3 sectored text winds
####################################################################

$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/smos.sectored.text_winds.sh
curr_retval=$?
retval=$((curr_retval+retval))
echo $retval
check_returns $retval $output_image

####################################################################
# 1.3.3 unsectored text winds
####################################################################

$GEOIPS_PACKAGES_DIR/geoips/tests/scripts/smap.unsectored.text_winds.sh
curr_retval=$?
retval=$((curr_retval+retval))
echo $retval
check_returns $retval $output_image

####################################################################
# 1.3.1 HY-2 Reader, hy2b
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_hy2/data/hscat_20211202_080644_hy_2b__15571_o_250_2204_ovw_l2.nc \
             --reader_name scat_knmi_winds_netcdf \
             --product_name windspeed \
             --minimum_coverage 0 \
             --output_formatter imagery_annotated \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/windspeed/hscat/20211202.080644.hy-2b.hscat.windspeed.global.6p83.knmi.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*hy*
check_returns $retval $output_image

####################################################################
# NOTE Currently no sample test case for Level 2 ABI reader
####################################################################

####################################################################
# ABI Reader - GOES-17
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_abi_day/data/goes17_20210718_0150/OR_ABI-L1b-RadF-M6C14_G17_s20211990150319_e20211990159386_c20211990159442.nc \
             --reader_name abi_netcdf \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/abi/20210718.015031.goes-17.abi.Infrared-Gray.global.22p79.noaa.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*goes-17*
check_returns $retval $output_image

####################################################################
# ABI Reader - GOES-16
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/goes16/20200918/1950/OR_ABI-L1b-RadF-M6C14_G16_s20202621950205_e20202621959513_c20202622000009.nc \
             --reader_name abi_netcdf \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/abi/20200918.195020.goes-16.abi.Infrared-Gray.global.22p84.noaa.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*goes-16*
check_returns $retval $output_image

####################################################################
# AHI Reader
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0110.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0210.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0310.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0410.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0510.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0610.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0710.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0810.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S0910.DAT \
             $GEOIPS_TESTDATA_DIR/test_data_ahi_day/data/20200405_0000/HS_H08_20200405_0000_B13_FLDK_R20_S1010.DAT \
             --reader_name ahi_hsd \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/ahi/20200405.000000.himawari-8.ahi.Infrared-Gray.global.29p98.jma.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*ahi*
check_returns $retval $output_image

####################################################################
# EWS-G Reader
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_ewsg/data/2020.1211.2312.goes-13.gvar.nc \
             --reader_name ewsg_netcdf \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/gvar/20201211.230905.ews-g.gvar.Infrared-Gray.global.33p25.noaa.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*ews*
check_returns $retval $output_image

####################################################################
# SEVIRI HRIT Reader - MSG-1
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-_________-EPI______-202004040800-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-_________-PRO______-202004040800-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000001___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000002___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000003___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000004___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000005___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000006___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000007___-202004040800-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20200404.0800_meteoIO_tc2020sh24irondro/H-000-MSG1__-MSG1_IODC___-IR_108___-000008___-202004040800-C_ \
             --reader_name seviri_hrit\
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/seviri/20200404.080000.msg-1.seviri.Infrared-Gray.global.22p84.nesdisstar.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $avfunc/*msg-1*
check_returns $retval $output_image

####################################################################
# SEVIRI HRIT Reader - MSG-4
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-_________-EPI______-202202092200-__ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000001___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000002___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000003___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000004___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000005___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000006___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000007___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-IR_108___-000008___-202202092200-C_ \
             $GEOIPS_TESTDATA_DIR/test_data_seviri/data/20220209.2200_meteoEU/H-000-MSG4__-MSG4________-_________-PRO______-202202092200-__ \
             --reader_name seviri_hrit\
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/seviri/20220209.220000.msg-4.seviri.Infrared-Gray.global.22p84.nesdisstar.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $avfunc/*msg-4*
check_returns $retval $output_image

#######################################################################
# NOTE Currently no sample test case for WFABBA ASCII ABI Fire Product
#######################################################################

####################################################################
# MODIS Reader - Aqua
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/200500/MYD021KM.A2021004.2005.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/200500/MYD03.A2021004.2005.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201000/MYD021KM.A2021004.2010.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201000/MYD03.A2021004.2010.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201500/MYD021KM.A2021004.2015.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/aqua/20210104/201500/MYD03.A2021004.2015.061.NRT.hdf \
             --reader_name modis_hdf4 \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/modis/20210104.201500.aqua.modis.Infrared-Gray.global.2p08.nasa.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $avfunc/*aqua*
check_returns $retval $output_image

####################################################################
# MODIS Reader - Terra
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_modis/data/terra/170500/MOD021KM.A2021004.1705.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/terra/170500/MOD03.A2021004.1705.061.NRT.hdf \
             $GEOIPS_TESTDATA_DIR/test_data_modis/data/terra/170500/MOD14.A2021004.1705.006.NRT.hdf \
             --reader_name modis_hdf4 \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/modis/20210104.170500.terra.modis.Infrared-Gray.global.0p63.nasa.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $avfunc/*terra*
check_returns $retval $output_image

####################################################################
# VIIRS Reader - JPSS
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ102IMG.A2021040.0736.002.2021040145245.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/073600/VJ103IMG.A2021040.0736.002.2021040142228.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ102IMG.A2021040.0742.002.2021040143010.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/jpss/20210209/074200/VJ103IMG.A2021040.0742.002.2021040140938.nc \
             --reader_name viirs_netcdf \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/viirs/20210209.074210.jpss-1.viirs.Infrared-Gray.global.2p00.NASA.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*jpss*
check_returns $retval $output_image

####################################################################
# VIIRS Reader - NPP
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20210205/080600/VNP02DNB.A2021036.0806.001.2021036140558.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20210205/080600/VNP02IMG.A2021036.0806.001.2021036140558.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20210205/080600/VNP02MOD.A2021036.0806.001.2021036140558.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20210205/080600/VNP03DNB.A2021036.0806.001.2021036135524.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20210205/080600/VNP03IMG.A2021036.0806.001.2021036135524.nc \
             $GEOIPS_TESTDATA_DIR/test_data_viirs/data/npp/20210205/080600/VNP03MOD.A2021036.0806.001.2021036135524.nc \
             --reader_name viirs_netcdf \
             --product_name Infrared-Gray \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --resampled_read \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/Infrared-Gray/viirs/20210205.080611.npp.viirs.Infrared-Gray.global.0p97.NASA.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*npp*
check_returns $retval $output_image

#######################################################################
# NOTE Currently no sample test case for AMSR2 Reader
#######################################################################

#######################################################################
# NOTE Currently no sample test case for AMSR2 REMSS Winds Reader
#######################################################################

#######################################################################
# NOTE Currently no sample test case for AMSU-A/AMSU-B/MHS HDF Reader
#######################################################################

#######################################################################
# NOTE Currently no sample test case for AMSU-A/AMSU-B/MHS MIRS Reader
#######################################################################

####################################################################
# GMI Reader
####################################################################

geoips run single_source $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S171519-E172017.V05A.RT-H5 \
             $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S172019-E172517.V05A.RT-H5 \
             $GEOIPS_TESTDATA_DIR/test_data_gpm/data/1B.GPM.GMI.TB2016.20200917-S172519-E173017.V05A.RT-H5 \
             --reader_name gmi_hdf5 \
             --product_name 89H \
             --output_formatter imagery_annotated \
             --minimum_coverage 0 \
             --filename_formatter geoips_fname \
             --sector_list global_cylindrical
curr_retval=$?
echo ""
output_image=$globdir/89H/gmi/20200917.171519.GPM.gmi.89H.global.0p84.NASA.20p0.png
cp -v $output_image $avfunc
cp_retval=$?
retval=$((curr_retval+cp_retval+retval))
ls -lh $GEOIPS_PACKAGES_DIR/geoips/docs/images/available_functionality/*gmi*
check_returns $retval $output_image


exit $retval
