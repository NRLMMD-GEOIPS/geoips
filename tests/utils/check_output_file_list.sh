# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# Default value for copy_dir so script does not fail if copy_dir undefined.
expected_outputs=${1:-${expected_outputs:-''}}
copy_dir=${2:-${copy_dir:-''}}

echo "expected_outputs: $expected_outputs"
echo "copy_dir: $copy_dir"
echo ""
echo "Call from final directory:"
echo "bash $0 $expected_outputs $copy_dir"
echo ""
echo "Call from temp output file list directory:"
echo "bash $0 ${expected_outputs/output_file_list/output_file_list_temp_current/} $copy_dir"
echo ""
# Ensure all output paths have any defined GEOIPS_REPLACE_OUTPUT_PATHS replaced with
# the defaults for test consistency.
# See geoips/geoips/filenames/base_paths.py for more information on
# GEOIPS_REPLACE_OUTPUT_PATHS
echo "GEOIPS_REPLACE_OUTPUT_PATHS: $GEOIPS_REPLACE_OUTPUT_PATHS"
echo "Available output paths:"
for replace_path_env_var in $GEOIPS_REPLACE_OUTPUT_PATHS; do
    replace_path=${!replace_path_env_var} 
    if [[ "${replace_path}" != "" ]]; then
        echo "    $replace_path_env_var: $replace_path"
    fi
done

if [[ ! -f $expected_outputs ]]; then
    echo "Expected outputs file does not exist, please create before comparing output filenames with list: $expected_outputs"
    exit 1
fi

    # List of output products to check if they were produced
    echo Verifying config-based processing produced the correct products:
    echo
    exit_state=0
    while read filename; do
        # Use the list of GEOIPS_REPLACE_OUTPUT_PATHS as specified in the environment.
        # List must be used for all output metadata and tests to ensure consistency.
        # Note for python-based processing GEOIPS_REPLACE_OUTPUT_PATHS is automatically
        # defaulted in geoips/geoips/filenames/base_paths.py, but must be set in the
        # environment when using this test comparison script.
        fname=$filename
        for replace_path_env_var in $GEOIPS_REPLACE_OUTPUT_PATHS; do
           replace_path=${!replace_path_env_var} 
           fname="${fname/'$'$replace_path_env_var/$replace_path}"
        done
        # Replace non-output-path based env vars.  This should match the order listed
        # in geoips/geoips_utils.py
        fname="${fname/'$GEOIPS_OUTDIRS'/$GEOIPS_OUTDIRS}"
        fname="${fname/'$GEOIPS_PACKAGES_DIR'/$GEOIPS_PACKAGES_DIR}"
        fname="${fname/'$GEOIPS_TESTDATA_DIR'/$GEOIPS_TESTDATA_DIR}"
        fname="${fname/'$GEOIPS_DEPENDENCIES_DIR'/$GEOIPS_DEPENDENCIES_DIR}"
        fname="${fname/'$GEOIPS_BASEDIR'/$GEOIPS_BASEDIR}"
        if [[ -f "$fname" ]]; then
            echo "FOUNDPRODUCT $filename"
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
            echo "MISSINGPRODUCT $filename"
            echo "*******************************************"
            exit_state=1
        fi
    done < $expected_outputs

echo "Number outputs expected: "`wc -l $expected_outputs| cut -d " " -f 1`
echo "Return code for output file list comparison: $exit_state"
exit $exit_state
