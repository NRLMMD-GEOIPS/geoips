# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
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

# simple bash script to track a pid while process is running

pid=$1

echo "Tracking usage statistics for pid ${pid}"

csv_header="Time [UTC], CPU Count, CPU Percent, Thread Count, USS [RAM bytes], RSS [bytes]"

# check that the output directory exists
outdir="${GEOIPS_OUTDIRS}/memory_logs/"

if [[ ! -d $outdir ]]; then
    echo "Making $GEOIPS_OUTDIRS/memory_logs"
    mkdir $outdir
fi

outname="geoips_memtrack_p${pid}.csv"
outpath="${outdir}/${outname}"


echo $csv_header >> ${outpath}

while ps -p $pid > /dev/null; do

    dtime=$(date +%Y%m%d_%H%M%S_%N)
    memstats=$(python $GEOIPS_PACKAGES_DIR/geoips/geoips/utils/memusg.py ${pid})

    echo "${dtime},${memstats}" >> ${outpath}

    # could be adjusted
    sleep 0.1

done

echo "Finished tracking, see csv file in ${outpath} for results"