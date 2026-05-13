# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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
if [[ "$7" == "" && -z "$GEOIPS_OUTDIRS" ]]; then
    bad_command=1
fi

if [[ "$8" == "" && -z "$GEOIPS_PACKAGES_DIR" ]]; then
    bad_command=1
fi

if [[ "$1" == "" || "$bad_command" == "1" ]]; then
    echo "Usage: $0 <satellite> YYYY MM DD HH MN <testdata_dir> <rclone_conf> <collection> <wildcard_list>"
    echo "    satellite:"
    echo "        goes16"
    echo "        goes17"
    echo "        himawari8"
    echo "        himawari9"
    echo "        geokompsat"
    echo "        noaa-20"
    echo "        noaa-21"
    echo "        snpp"
    echo "        jpss"
    echo "    testdata_dir: "
    echo "        if 'default' or not specified, defaults to: "
    echo "       \$GEOIPS_OUTDIRS/noaa_aws_downloads/data/<satellite>/<YYYYmmdd>/<HHMN>"
    echo "    rclone_conf: "
    echo "        if 'default' or not specified, defaults to:"
    echo "        \$GEOIPS_PACKAGES_DIR/geoips/setup/rclone_setup/rclone.conf"
    echo "    collection:"
    echo "        If not defined, defaults to L1B full disk for geostationary"
    echo "        Since there are so many NOAA/NPP products, no sensible default.."
    echo "        This refers to the initial subdirectory found in the NOAA AWS"
    echo "          S3 buckets (prior to the date-based subdirs)"
    echo "          ie: noaa-nesdis-snpp-pds.s3.amazonaws.com/VIIRS-IMG-GEO-TC"
    echo "        examples of collections (you can find all available collections"
    echo "          by navigating the S3 buckets on the web)"
    echo "        viirs"
    echo "           VIIRS-IMG-GEO-TC"
    echo "           VIIRS-I5-SDR"
    echo "        ahi"
    echo "           AHI-L1b-FLDK"
    echo "    wildcard_list: "
    echo "        list of strings to match in filenames (ie, channels)."
    echo "        Defaults to all files for dtg"
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
    testdata_dir="$GEOIPS_OUTDIRS/noaa_aws_downloads/data/$satellite/$yyyy$mm$dd/$hh$mn"
else
    testdata_dir="$7"
fi
if [[ "$8" == "" || "$8" == "default" ]]; then
    rclone_conf="$GEOIPS_PACKAGES_DIR/geoips/setup/rclone_setup/rclone.conf"
else
    rclone_conf="$8"
fi
if [[ "$9" == "" || "$9" == "default" ]]; then
    collection=""
else
    collection=$9
fi
wildcard_list=${10:-""}

mkdir -p $testdata_dir

if [[ "$satellite" == "himawari8" || "$satellite" == "himawari9" ]]; then
    collection=${collection:-"AHI-L1b-FLDK"}
    rclone_path="publicAWS:noaa-$satellite/$collection/$yyyy/$mm/$dd/$hh$mn/"
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
elif [[ "$satellite" == "geokompsat" ]]; then
    collection=${collection:-"AMI/L1B/FD"}
    rclone_path="publicAWS:noaa-gk2a-pds/$collection/$yyyy$mm/$dd/$hh/"
    echo "rclone --config $rclone_conf lsf $rclone_path"
    files=`rclone --config $rclone_conf lsf $rclone_path`
    echo "COMPARE: ${yyyy}${mm}${dd}${hh}${mn}"
    for fname in $files; do
        if [[ "$fname" =~ "${yyyy}${mm}${dd}${hh}${mn}" ]]; then
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
        fi
    done
elif [[ "$satellite" == "noaa-20" || "$satellite" == "noaa-21" || "$satellite" == "jpss" || "$satellite" == "snpp" ]]; then
    collection=${collection:-"VIIRS-I1-SDR"}
    # https://noaa-nesdis-n20-pds.s3.amazonaws.com/VIIRS-I1-SDR/2024/08/07/SVI01_j01_d20240807_t0000596_e0002241_b34811_c20240807002901054000_oebc_ops.h5
    if [[ "$satellite" == "noaa-20" ]]; then
        resource_name="noaa-nesdis-n20-pds"
    elif [[ "$satellite" == "noaa-21" ]]; then
        resource_name="noaa-nesdis-n21-pds"
    elif [[ "$satellite" == "snpp" ]]; then
        resource_name="noaa-nesdis-snpp-pds"
    elif [[ "$satellite" == "jpss" ]]; then
        resource_name="noaa-nesdis-jpss"
    fi
    rclone_path="publicAWS:$resource_name/$collection/$yyyy/$mm/$dd/"
    echo ""
    echo "************************************************************************************************************"
    echo "URL listing available files: https://${resource_name}.s3.amazonaws.com/index.html#$collection/$yyyy/$mm/$dd/"
    echo "************************************************************************************************************"
    echo ""
    echo "rclone --config $rclone_conf lsf $rclone_path"
    files=`rclone --config $rclone_conf lsf $rclone_path`
    echo "COMPARE: d${yyyy}${mm}${dd}_t${hh}${mn}"
    for fname in $files; do
        if [[ "$fname" =~ "d${yyyy}${mm}${dd}_t${hh}${mn}" ]]; then
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
        fi
    done
elif [[ "$satellite" == "gfs" ]]; then
    # https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20221019/00/atmos/gfs.t00z.pgrb2.0p25.f000
    collection=${collection:-"atmos"}
    resource_name="noaa-gfs-bdp-pds"
    rclone_path="publicAWS:$resource_name/gfs.${yyyy}${mm}${dd}/$hh/$collection"
    echo ""
    echo "************************************************************************************************************"
    echo "URL listing available files: https://${resource_name}.s3.amazonaws.com/index.html#gfs.${yyyy}${mm}${dd}/$hh/$collection/"
    echo "************************************************************************************************************"
    echo ""
    echo "rclone --config $rclone_conf lsf $rclone_path"
    files=`rclone --config $rclone_conf lsf $rclone_path`
    echo "COMPARE: gfs.t${hh}z.pgrb2.0p25"
    if [[ "$wildcard_list" == "" ]]; then
        # Only download analysis if wildcard_list is not defined
        wildcard_list="anl"
    fi
    for fname in $files; do
        if [[ "$fname" =~ "gfs.t${hh}z.pgrb2.0p25" ]]; then
            for wildcard in "$wildcard_list"; do
                if [[ "$fname" =~ "$wildcard" ]]; then
                    echo "rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/"
                    rclone --config $rclone_conf copy -P $rclone_path/$fname $testdata_dir/
                fi
            done
        fi
    done
else
    collection=${collection:-"ABI-L1b-RadF"}
    rclone_path="publicAWS:noaa-$satellite/$collection/$yyyy/$jday/$hh/"
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
