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
# rclone lsf publicAWS:noaa-goes16/ABI-L1b-RadF/2020/184/16/
# rclone lsf publicAWS:noaa-goes17/ABI-L1b-RadF/2020/184/16/
# rclone lsf publicAWS:noaa-himawari8/AHI-L1b-FLDK/2022/02/05/0420

date_cmd=date
if [[ $OSTYPE == 'darwin'* ]]; then
    date_cmd="$(which gdate)"
    if [[ $? -ne 0 ]]; then
        echo "On Mac, please install gdate. For example, brew install coreutils."
        exit 1
    fi
fi

bad_command=0
if [[ "$7" == "" && -z "$GEOIPS_TESTDATA_DIR" ]]; then
    bad_command=1
fi

if [[ "$8" == "" && -z "$GEOIPS_PACKAGES_DIR" ]]; then
    bad_command=1
fi

if [[ "$1" == "" || "$bad_command" == "1" ]]; then
    echo "Usage: $0 <satellite> YYYY MM DD HH MN <testdata_dir> <rclone_conf>"
    echo "    satellite: goes16, goes17, himawari8"
    echo "    testdata_dir: if 'default' or not specified, defaults to: "
    echo "       \$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/<satellite>/<YYYYmmdd>/<HHMN>"
    echo "    rclone_conf: if 'default' or not specified, defaults to:"
    echo "        \$GEOIPS_PACKAGES_DIR/geoips/setup/rclone_setup/rclone.conf"
    echo "    wildcard_list: list of strings to match in filenames (ie, channels). Defaults to all files for dtg"
    exit 1
fi

satellite=$1
yyyy=$2
mm=$3
dd=$4
hh=$5
mn=$6

jday=`$date_cmd -u -d "$yyyy-$mm-$dd $hh:$mn:00" +%j`

if [[ "$7" == "" || "$7" == "default" ]]; then
    testdata_dir="$GEOIPS_TESTDATA_DIR/test_data_noaa_aws/data/$satellite/$yyyy$mm$dd/$hh$mn"
else
    testdata_dir="$7"
fi
if [[ "$8" == "" || "$8" == "default" ]]; then
    rclone_conf="$GEOIPS_PACKAGES_DIR/geoips/setup/rclone_setup/rclone.conf"
else
    rclone_conf="$8"
fi
if [[ "$9" == "" ]]; then
    wildcard_list=""
else
    wildcard_list="$9"
fi

mkdir -p $testdata_dir

if [[ "$satellite" == "himawari8" ]]; then
    rclone_path="publicAWS:noaa-himawari8/AHI-L1b-FLDK/$yyyy/$mm/$dd/$hh$mn/"
    echo "rclone --config $rclone_conf lsf $rclone_path"
    files=`rclone --config $rclone_conf lsf $rclone_path`
    for fname in $files; do
        if [[ "$wildcard_list" == "" ]]; then
            echo "rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/"
            rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/
        else
            for wildcard in $wildcard_list; do
                if [[ "$fname" =~ "$wildcard" ]]; then
                    echo "rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/"
                    rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/
                fi
            done
        fi
    done
else
    rclone_path="publicAWS:noaa-$satellite/ABI-L1b-RadF/$yyyy/$jday/$hh/"
    echo "rclone --config $rclone_conf lsf $rclone_path"
    files=`rclone --config $rclone_conf lsf $rclone_path`
    for fname in $files; do
        if [[ "$fname" =~ "s$yyyy$jday$hh$mn" ]]; then
            # Grab all of the files for that dtg
            if [[ "$wildcard_list" == "" ]]; then
                echo "rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/"
                rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/
            else
                # Only grab files matching "$wildcard"
                for wildcard in $wildcard_list; do
                    if [[ "$fname" =~ "$wildcard" ]]; then
                        echo "rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/"
                        rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/
                    fi
                done
            fi
        fi
    done
fi
