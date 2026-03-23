# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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