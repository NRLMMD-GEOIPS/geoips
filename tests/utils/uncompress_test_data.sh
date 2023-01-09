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

#!/bin/bash

data_path=$1
decompress_type=$2

if [[ "$1" == "" || "$2" == "" ]]; then
    echo "Usage: $0 <data_path> <decompress_type>"
    echo "Where:"
    echo "      data_path: full path to base directory containing data files"
    echo "                 (looks 3 levels down for files to decompress)"
    echo "      deompress_type: One of:"
    echo "          gunzip"
    echo "          bunzip2"
    echo "          tgz"
    exit 1
fi

if [[ "$decompress_type" == "gunzip" ]]; then
    echo "Checking for gz files in $data_path/*.gz..."
    date -u
    if ls $data_path/*.gz >& /dev/null; then
        echo "    gunzip $data_path/*.gz"
        gunzip -f $data_path/*.gz
    fi
    
    echo "Checking for gz files in $data_path/*/*.gz..."
    date -u
    if ls $data_path/*/*.gz >& /dev/null; then
        echo "    gunzip $data_path/*/*.gz"
        gunzip -f $data_path/*/*.gz
    fi
    
    echo "Checking for gz files in $data_path/*/*/*.gz..."
    date -u
    if ls $data_path/*/*/*.gz >& /dev/null; then
        echo "    gunzip $data_path/*/*/*.gz"
        gunzip -f $data_path/*/*/*.gz
    fi
fi

if [[ "$decompress_type" == "bunzip2" ]]; then
    echo "Checking for bz2 files in $data_path/*.bz2..."
    date -u
    if ls $data_path/*.bz2 >& /dev/null; then
        echo "    bunzip2 $data_path/*.bz2"
        bunzip2 -f $data_path/*.bz2
    fi

    echo "Checking for bz2 files in $data_path/*/*.bz2..."
    date -u
    if ls $data_path/*/*.bz2 >& /dev/null; then
        echo "    bunzip2 $data_path/*/*.bz2"
        bunzip2 -f $data_path/*/*.bz2
    fi

    echo "Checking for bz2 files in $data_path/*/*/*.bz2..."
    date -u
    if ls $data_path/*/*/*.bz2 >& /dev/null; then
        echo "    bunzip2 $data_path/*/*/*.bz2"
        bunzip2 -f $data_path/*/*/*.bz2
    fi
fi

if [[ "$decompress_type" == "tgz" ]]; then
    echo "Checking for tgz files in $data_path/*.tgz..."
    if ls $data_path/*.tgz >& /dev/null; then
        for tgz_fname in $data_path/*.tgz; do
            date -u
            echo "   Trying $tgz_fname..."
            if [[ ! -e ${tgz_fname%.*} ]]; then
                echo "    tar -xzf $tgz_fname -C `dirname $tgz_fname`"
                tar -xzf $tgz_fname -C `dirname $tgz_fname`
            else
                echo "    Already decompressed"
            fi
        done
    fi
    echo "Checking for tgz files in $data_path/*/*.tgz..."
    if ls $data_path/*/*.tgz >& /dev/null; then
        for tgz_fname in $data_path/*/*.tgz; do
            date -u
            echo "   Trying $tgz_fname..."
            if [[ ! -e ${tgz_fname%.*} ]]; then
                echo "    tar -xzf $tgz_fname -C `dirname $tgz_fname`"
                tar -xzf $tgz_fname -C `dirname $tgz_fname`
            else
                echo "    Already decompressed"
            fi
        done
    fi
    echo "Checking for tgz files in $data_path/*/*/*.tgz..."
    if ls $data_path/*/*/*.tgz >& /dev/null; then
        for tgz_fname in $data_path/*/*/*.tgz; do
            date -u
            echo "   Trying $tgz_fname..."
            if [[ ! -e ${tgz_fname%.*} ]]; then
                echo "    tar -xzf $tgz_fname -C `dirname $tgz_fname`"
                tar -xzf $tgz_fname -C `dirname $tgz_fname`
            else
                echo "    Already decompressed"
            fi
        done
    fi
fi
