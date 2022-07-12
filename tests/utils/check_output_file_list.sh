# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # # 
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # # 
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # # 
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # # 
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

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
        else   
            echo "*******************************************"
            echo "MISSINGPRODUCT $fname"
            echo "*******************************************"
            exit_state=1
        fi
    done < $expected_outputs

echo "Number outputs expected: "`wc -l $expected_outputs| cut -d " " -f 1`
echo "Return code for product comparison: $exit_state"
