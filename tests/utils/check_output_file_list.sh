# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# Default value for copy_dir so script does not fail if copy_dir undefined.
expected_outputs=${1:-${expected_outputs:-''}}
copy_dir=${2:-${copy_dir:-''}}
tmp_outdirs=${3:-${tmp_outdirs:-''}}

echo "expected_outputs: $expected_outputs"
echo "copy_dir: $copy_dir"
echo "tmp_outdirs: $tmp_outdirs"

if [[ "$tmp_outdirs" == "" ]]; then
    tmp_outdirs=$GEOIPS_OUTDIRS
fi

if [[ ! -f $expected_outputs ]]; then
    echo "Expected outputs file does not exist, please create before running test: $expected_outputs"
    exit 1
fi

    # List of output products to check if they were produced
    echo Verifying config-based processing produced the correct products:
    echo
    exit_state=0
    while read filename; do
        fname="${filename/'$GEOIPS_OUTDIRS'/$tmp_outdirs}"
        if [[ -f "$fname" ]]; then
            echo "FOUNDPRODUCT $fname"
            if [[ "$copy_dir" != "" && -d $copy_dir ]]; then
                copy_fname=`basename $fname`
                unzipped_fname=""
                if [[ `basename $fname` == *"."* ]]; then
                    ext="${fname##*.}"
                else
                    ext="noext"
                fi
                if [[ "$ext" == "gz" ]]; then
                    # Copy the original unzipped file first, to ensure we have the original
                    mkdir -p $copy_dir/$ext
                    echo "    cp $fname $copy_dir/$ext/$copy_fname"
                    cp $fname $copy_dir/$ext/$copy_fname

                    # Now unzip file, for easy viewing
                    gunzip $fname
                    unzipped_fname="${fname%.*}"
                    ext="${unzipped_fname##*.}"

                    # If it is a "jif" file, copy it as a "tif" for easy viewing
                    if [[ "$ext" == "jif" ]]; then
                        copy_fname=`basename "${unzipped_fname%.*}.tif"`
                    fi
                    fname=$unzipped_fname
                fi

                # Now copy the final easy-to-view file
                mkdir -p $copy_dir/$ext
                echo "    cp $fname $copy_dir/$ext/$copy_fname"
                cp $fname $copy_dir/$ext/$copy_fname

                # Now if we had unzipped the original file, re-zip it so we leave things how we found them.
                if [[ "$unzipped_fname" != "" ]]; then
                    echo "gzip $unzipped_fname"
                    gzip $unzipped_fname
                fi
            fi
        else   
            ext="${fname##*.}"
            if [[ "$ext" == "gz" ]]; then
                unzipped_fname="${fname%.*}"
                if [[ -f "$unzipped_fname" ]]; then
                    echo "gzip $unzipped_fname"
                    gzip $unzipped_fname
                fi
            fi
            echo "*******************************************"
            echo "MISSINGPRODUCT $fname"
            echo "*******************************************"
            exit_state=1
        fi
    done < $expected_outputs

echo "Number outputs expected: "`wc -l $expected_outputs| cut -d " " -f 1`
echo "Return code for product comparison: $exit_state"
